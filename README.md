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

## 一些可以做的实验
1. 看一下我们的路径计算方式的普适性，也就是在大拓扑下的表现，首先看计算初始备份路径要多久，然后是某一条边发生故障时的平均计算时延。
2. 和最优路径的比较肯定是要比的。我觉得我们在路径选择的时候，应该对s和d有个限定，比如只能是edge和core，不能是aggregation，因为aggregation不太符合常理。
3. 内存的开销也肯定是要比的。
4. packet loss也是一个指标，不过按理来说我们通常是不会丢包的。除非出现了循环导致ttl耗尽的情况，要测也是可以测的。可以考虑和reactive的方式比，这种是会导致丢包的。
5. 比故障的恢复率，比如有的文章为了减少存的规则，不考虑备份路径故障的问题，或者有的文章考虑了备份路径故障的问题，但这时导致他们的内存开销很大。其实这两种情况都是不如我们的！我们理论上可以进行无限的故障恢复，只要这个点真的是可达的。  同时，我们也可以测一下在我们的系统中不同的备份路径长度限制对故障恢复率的影响，甚至来动态调整这个东西达到一个较优的效果。
6. 感觉latency也可以比，因为加头部和处理头部导致的开销 和 控制器下发规则相比。可以让故障恢复前后走的路径长度都一样，就用那个最经典的菱形测试就可以，一个走上，一个走下，看看延迟差距，然后再让控制器下发规则看看差距。
7. SlickFlow的Eval.D很不错，完全可以借鉴。

## Memo
1. 在控制器处理连接恢复的逻辑中，路径的恢复只将恢复的路径重新加入到backup_path中即可。因为我们这个系统不支持新加连接，所以如果之前找不到备份路径了，那唯一修复的可能就是把那个端口修好。所以这里不需要任何的实际交换机配置。在没修好之前，利用以前的故障恢复路径，只可能会造成无限循环，在ttl到期后被抛弃。这里只是有可能是因为另一端有可能有新的恢复路径了，就不再回我这里，自然就走了。

2. 在容器的网卡上已经收到了iperf的数据包了，但是iperf应用程序并没有收到，在这个过程中是哪个步骤出现了问题？是网卡？还是docker？

3. 现在计算路径使用的方式是dijkstra算法，其实可以使用更优秀的算法使得link负载均衡，从而使得吞吐率什么的不会下降很多。可以算作future work