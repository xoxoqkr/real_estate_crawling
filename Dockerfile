# Python 3.9 기반 이미지 사용
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 파일 복사
COPY . .

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    ca-certificates \
    software-properties-common \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libappindicator1 \
    libayatana-indicator7 \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    && apt-get clean

# 최신 Google Chrome 저장소 키 추가
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list

# Google Chrome 133.0.6943.98 설치
RUN apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Chrome 실행 파일 확인 (디버깅용)
RUN which google-chrome || echo "Chrome binary not found"
RUN ls -l /usr/bin/google-chrome || echo "Chrome binary not found"
RUN google-chrome --version || echo "Chrome installation failed"

# ChromeDriver 133.0.6943.98 다운로드 및 설치
RUN wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/133.0.6943.98/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver* \
    && chmod +x /usr/local/bin/chromedriver

# ChromeDriver 실행 파일 확인 (디버깅용)
RUN which chromedriver || echo "ChromeDriver binary not found"
RUN chromedriver --version || echo "ChromeDriver installation failed"

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 실행 명령어
CMD ["python", "src/main.py"]
