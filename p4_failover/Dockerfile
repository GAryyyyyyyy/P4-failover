FROM ubuntu:trusty

WORKDIR /home/root

RUN apt update
RUN apt install -y python python-pip iperf iperf3
RUN pip install scapy

CMD ["/bin/bash"]
