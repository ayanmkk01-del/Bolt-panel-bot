FROM python:3.10-slim

# Chrome এবং dependencies ইনস্টল করুন
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver ইনস্টল করুন
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    CHROME_MAJOR_VERSION=${CHROME_VERSION%.*.*} && \
    wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# কাজের ডিরেক্টরি
WORKDIR /app

# Python dependencies কপি ও ইনস্টল
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# কোড কপি করুন
COPY bolt.py .

# আউটপুট দেখার জন্য
ENV PYTHONUNBUFFERED=1

# বট রান করুন
CMD ["python", "-u", "bolt.py"]