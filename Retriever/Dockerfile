FROM public.ecr.aws/lambda/python:3.11

# 작업 디렉토리 설정
WORKDIR /var/task

# 필요한 시스템 패키지 설치
RUN yum update -y && yum install -y gcc-c++

# requirements.txt 복사 및 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.3.1 && \
    pip install --no-cache-dir -r requirements.txt

# Lambda 함수 코드 복사
COPY lambda_function.py .

# Lambda 핸들러 지정
CMD ["lambda_function.lambda_handler"]