FROM xarthisius/girder:latest
MAINTAINER Kacper Kowalik <xarthisius.kk@gmail.com>

COPY ./plugin.yml /girder/plugins/ythub/plugin.yml
COPY ./requirements.txt /girder/plugins/ythub/requirements.txt
COPY ./server /girder/plugins/ythub/server
COPY ./web_client /girder/plugins/ythub/web_client

RUN pip install -r plugins/ythub/requirements.txt
RUN girder-install web --plugins='ythub'

COPY ./girder.local.cfg /girder/girder/conf/girder.local.cfg
