FROM collectorbase_collector_env:latest
MAINTAINER "Cloudsoar Registry Collector"

USER root

############################################################
# Setup environment variables
############################################################
ENV WORK_DIR /opt
ENV INSTALL_SCRIPT /opt/DockerCollector/install.sh
ENV START_SCRIPT /opt/startService.sh

############################################################

# Create dirs
RUN mkdir -p  $WORK_DIR/DockerCollector 

# Add dirs
ADD DockerCollector $WORK_DIR/DockerCollector
ADD startService.sh $START_SCRIPT

############################################################
# start mongodb
############################################################

RUN chmod +x $INSTALL_SCRIPT  && \
    chmod +x $START_SCRIPT 



############################################################
# 
############################################################

RUN cd $WORK_DIR/DockerCollector && \
    ./install.sh -i
 

# Let people know how this was built
ADD Dockerfile /root/Dockerfile

# Exposed ports
EXPOSE 80 27017

ENTRYPOINT 

CMD $START_SCRIPT
