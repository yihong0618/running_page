FROM python:3.10.5-slim
WORKDIR /root/running_page
COPY ./requirements.txt /root/running_page/requirements.txt
RUN sed -i 's@http://archive.ubuntu.com/ubuntu/@https://mirrors.tuna.tsinghua.edu.cn/ubuntu/@g' /etc/apt/sources.list \
  && sed -i 's@http://security.ubuntu.com/ubuntu/@https://mirrors.tuna.tsinghua.edu.cn/ubuntu/@g' /etc/apt/sources.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends git \
  && apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/* \
  && pip3 install -i https://mirrors.aliyun.com/pypi/simple/ pip -U \
  && pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
  && pip3 install -r requirements.txt
