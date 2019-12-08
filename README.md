# P4 failover program led by Fudan FNRG

## Dependencies
1. [P4 environment](https://github.com/p4lang)
2. [Containernet](https://github.com/containernet/containernet)
3. [Docker](https://www.docker.com/)

## Experiment todo
1. Effectiveness: 3 topos * 3 traces ---> packet loss rate (1 figure)
2. Compare with sigcomm 2018 workshop: throughput & hop count (2 figures)
3. Compare with reactive solutions: hop count & processing latency (2 figures)
4. Compare with proactive solutions: memory overhead (1 figure)
5. Optional: real world experiments: performance

## Experiment resources
1. [Aritel](http://www.topology-zoo.org/maps/Airtel.jpg)
2. [BT Asia-Pacific](http://www.topology-zoo.org/maps/BtAsiaPac.jpg)
3. [DataXchange](http://www.topology-zoo.org/maps/Dataxchange.jpg)
4. [Understanding Network Failures in Data Centers: Measurement, Analysis, and Implications](http://conferences.sigcomm.org/sigcomm/2011/papers/sigcomm/p350.pdf)
5. [iperf](https://iperf.fr/)

## Memo
1. 在控制器处理连接恢复的逻辑中，路径的恢复只将恢复的路径重新加入到backup_path中即可。因为我们这个系统不支持新加连接，所以如果之前找不到备份路径了，那唯一修复的可能就是把那个端口修好。所以这里不需要任何的实际交换机配置。在没修好之前，利用以前的故障恢复路径，只可能会造成无限循环，在ttl到期后被抛弃。这里只是有可能是因为另一端有可能有新的恢复路径了，就不再回我这里，自然就走了。

2. 在容器的网卡上已经收到了iperf的数据包了，但是iperf应用程序并没有收到，在这个过程中是哪个步骤出现了问题？是网卡？还是docker？