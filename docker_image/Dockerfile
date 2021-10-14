FROM python:3.8.10
WORKDIR /morphemic_project

RUN python -m pip install --upgrade pip
COPY forecasting-prophet/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

ADD https://gitlab.ow2.org/melodic/morphemic-preprocessor/-/archive/morphemic-rc1.5/morphemic-preprocessor-morphemic-rc1.5.tar.gz /var/lib/morphemic/

COPY forecasting-prophet/ ./

RUN cd /var/lib/morphemic/ \
    && tar -zxf morphemic-preprocessor-morphemic-rc1.5.tar.gz \
    && cd morphemic-preprocessor-morphemic-rc1.5 \
    && cd morphemic-datasetmaker && python3 setup.py install \ 
    && cd ../.. \
    && cp -R /var/lib/morphemic/morphemic-preprocessor-morphemic-rc1.5/amq-message-python-library /morphemic_project/forecasting-prophet/prophet/messaging \
    && rm -rf /var/lib/morphemic \
    && mkdir -p /logs

 CMD python /morphemic_project/forecasting-prophet/prophet/main.py > /logs/prophet.log 2>&1
