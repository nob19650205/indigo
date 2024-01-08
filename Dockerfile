# base image
FROM python:3.10 as builder

# upgrade pip
RUN pip install --upgrade pip &&\
    pip install streamlit numpy pandas requests
    
# production stage
FROM python:3.10-slim
USER root
LABEL maintainer="nobumasa@jp.ibm.com"
LABEL title="DPP Summary"

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin/streamlit /usr/local/bin/streamlit
WORKDIR /root
COPY *.py /root
RUN mkdir .streamlit
COPY config.toml /root/.streamlit

# port
EXPOSE 8501

# CMD streamlit run /root/main.py 
CMD streamlit run main.py
