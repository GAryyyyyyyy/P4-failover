#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_RECOVERYPATH = 0x1212;
const bit<16> TYPE_IPV4 = 0x800;
#define MAX_HOPS 32
#define MAX_PORTS 128
/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
typedef bit<4> backup_length_t;
typedef bit<15> bp_hop_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}
//recover
header recoveryPath_t {
    bit<1>    bos;
    bit<15>   edge;
}
header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}
struct metadata{
    bit<1>  out_port_status;
    bit<1>  cur_bos;
    bit<1>  need_recycle;
    bit<4>  port_backup_length; 
    bit<15>  out_edge;
    bit<15>  meta_bp_v1_hop;
    bit<15>  meta_bp_v2_hop;
    bit<15>  meta_bp_v3_hop;
    bit<15>  meta_bp_v4_hop;
    bit<15>  meta_bp_v5_hop;
    bit<15>  meta_bp_v6_hop;
    bit<15>  meta_bp_v7_hop;
    bit<15>  meta_bp_v8_hop;
}


struct headers {
    ethernet_t   ethernet;
    recoveryPath_t[MAX_HOPS] recoveryPath;
    ipv4_t       ipv4;
}
/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/
parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {
    state start {
        transition parse_ethernet;
    }
    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_RECOVERYPATH: parse_myRecoveryPath;
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }
    state parse_myRecoveryPath {
        packet.extract(hdr.recoveryPath.next);
        transition select(hdr.recoveryPath.last.bos) {
            1: parse_ipv4;
            default: parse_myRecoveryPath;
        }
    }
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition accept;
    }

}
/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {   
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/
control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    register< bit<1> >(MAX_PORTS) all_ports_status;//register define

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action try_ipv4_forward(egressSpec_t port) {
        standard_metadata.egress_spec = port;
        //更新逻辑应该放到update_mac_addr里统一做
        // hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        // hdr.ethernet.dstAddr = dstAddr;
        // hdr.ipv4.ttl = hdr.ipv4.ttl - 1; //不应该在这更新ttl
        all_ports_status.read(meta.out_port_status, (bit<32>)standard_metadata.egress_spec);
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            try_ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    action copy_path(backup_length_t length, bp_hop_t v1, bp_hop_t v2, bp_hop_t v3, bp_hop_t v4, bp_hop_t v5, bp_hop_t v6, bp_hop_t v7, bp_hop_t v8){
            meta.port_backup_length=length;
            meta.meta_bp_v1_hop=v1;
            meta.meta_bp_v2_hop=v2;
            meta.meta_bp_v3_hop=v3;
            meta.meta_bp_v4_hop=v4;
            meta.meta_bp_v5_hop=v5;
            meta.meta_bp_v6_hop=v6;
            meta.meta_bp_v7_hop=v7;
            meta.meta_bp_v8_hop=v8;
    }
    table port_backup_path {
        key = {
            standard_metadata.egress_spec: exact;
        }
        actions = {
            copy_path;
        }
    }

    table port_backup_path_fault {
        key = {
            standard_metadata.egress_spec: exact;
        }
        actions = {
            copy_path;
        }
    }

    action update_mac_addr(macAddr_t dstAddr) {
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
    }

    // table port_to_mac {
    //     key = {
    //         standard_metadata.egress_spec: exact;
    //     }
    //     actions = {
    //         update_mac_addr;
    //     }
    // }

    action recovery_forward(egressSpec_t port) {
        standard_metadata.egress_spec = port;
        all_ports_status.read(meta.out_port_status, (bit<32>)standard_metadata.egress_spec);
    }

    table edge_to_port {
        key = {
            meta.out_edge: exact;
        }
        actions = {
            recovery_forward;
        }
    }

    action recoveryPath_finish() {
        hdr.ethernet.etherType = TYPE_IPV4;
    }
    action update_ttl(){
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }
    action recoveryPath_nhop() {
        meta.out_edge = hdr.recoveryPath[0].edge;
        meta.cur_bos = hdr.recoveryPath[0].bos;
        hdr.recoveryPath.pop_front(1);
    }
    action add_header_normal_1(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH; //important!!
        hdr.recoveryPath.push_front(1);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[0].bos = 1;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
    }
    action add_header_normal_2(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(2);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 1;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
    }
    action add_header_normal_3(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(3);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[2].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 0;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
        hdr.recoveryPath[2].bos = 0;
        hdr.recoveryPath[2].edge = meta.meta_bp_v3_hop;
    }
    action add_header_normal_4(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(4);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[2].setValid();
        hdr.recoveryPath[3].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 0;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
        hdr.recoveryPath[2].bos = 0;
        hdr.recoveryPath[2].edge = meta.meta_bp_v3_hop;
        hdr.recoveryPath[3].bos = 1;
        hdr.recoveryPath[3].edge = meta.meta_bp_v4_hop;
    }
    action add_header_normal_5(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(5);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[2].setValid();
        hdr.recoveryPath[3].setValid();
        hdr.recoveryPath[4].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 0;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
        hdr.recoveryPath[2].bos = 0;
        hdr.recoveryPath[2].edge = meta.meta_bp_v3_hop;
        hdr.recoveryPath[3].bos = 0;
        hdr.recoveryPath[3].edge = meta.meta_bp_v4_hop;
        hdr.recoveryPath[4].bos = 1;
        hdr.recoveryPath[4].edge = meta.meta_bp_v5_hop;
    }
    action add_header_normal_6(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(6);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[2].setValid();
        hdr.recoveryPath[3].setValid();
        hdr.recoveryPath[4].setValid();
        hdr.recoveryPath[5].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 0;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
        hdr.recoveryPath[2].bos = 0;
        hdr.recoveryPath[2].edge = meta.meta_bp_v3_hop;
        hdr.recoveryPath[3].bos = 0;
        hdr.recoveryPath[3].edge = meta.meta_bp_v4_hop;
        hdr.recoveryPath[4].bos = 0;
        hdr.recoveryPath[4].edge = meta.meta_bp_v5_hop;
        hdr.recoveryPath[5].bos = 1;
        hdr.recoveryPath[5].edge = meta.meta_bp_v6_hop;
    }
    action add_header_normal_7(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(7);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[2].setValid();
        hdr.recoveryPath[3].setValid();
        hdr.recoveryPath[4].setValid();
        hdr.recoveryPath[5].setValid();
        hdr.recoveryPath[6].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 0;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
        hdr.recoveryPath[2].bos = 0;
        hdr.recoveryPath[2].edge = meta.meta_bp_v3_hop;
        hdr.recoveryPath[3].bos = 0;
        hdr.recoveryPath[3].edge = meta.meta_bp_v4_hop;
        hdr.recoveryPath[4].bos = 0;
        hdr.recoveryPath[4].edge = meta.meta_bp_v5_hop;
        hdr.recoveryPath[5].bos = 0;
        hdr.recoveryPath[5].edge = meta.meta_bp_v6_hop;
        hdr.recoveryPath[6].bos = 1;
        hdr.recoveryPath[6].edge = meta.meta_bp_v7_hop;
    }
    action add_header_normal_8(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(8);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[2].setValid();
        hdr.recoveryPath[3].setValid();
        hdr.recoveryPath[4].setValid();
        hdr.recoveryPath[5].setValid();
        hdr.recoveryPath[6].setValid();
        hdr.recoveryPath[7].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 0;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
        hdr.recoveryPath[2].bos = 0;
        hdr.recoveryPath[2].edge = meta.meta_bp_v3_hop;
        hdr.recoveryPath[3].bos = 0;
        hdr.recoveryPath[3].edge = meta.meta_bp_v4_hop;
        hdr.recoveryPath[4].bos = 0;
        hdr.recoveryPath[4].edge = meta.meta_bp_v5_hop;
        hdr.recoveryPath[5].bos = 0;
        hdr.recoveryPath[5].edge = meta.meta_bp_v6_hop;
        hdr.recoveryPath[6].bos = 0;
        hdr.recoveryPath[6].edge = meta.meta_bp_v7_hop;
        hdr.recoveryPath[7].bos = 1;
        hdr.recoveryPath[7].edge = meta.meta_bp_v8_hop;
    }

    action add_header_fault_1(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH; //important!!
        hdr.recoveryPath.push_front(1);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[0].bos = meta.cur_bos;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
    }
    action add_header_fault_2(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(2);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = meta.cur_bos;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
    }
    action add_header_fault_3(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(3);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[2].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 0;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
        hdr.recoveryPath[2].bos = meta.cur_bos;
        hdr.recoveryPath[2].edge = meta.meta_bp_v3_hop;
    }
    action add_header_fault_4(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(4);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[2].setValid();
        hdr.recoveryPath[3].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 0;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
        hdr.recoveryPath[2].bos = 0;
        hdr.recoveryPath[2].edge = meta.meta_bp_v3_hop;
        hdr.recoveryPath[3].bos = meta.cur_bos;
        hdr.recoveryPath[3].edge = meta.meta_bp_v4_hop;
    }
    action add_header_fault_5(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(5);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[2].setValid();
        hdr.recoveryPath[3].setValid();
        hdr.recoveryPath[4].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 0;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
        hdr.recoveryPath[2].bos = 0;
        hdr.recoveryPath[2].edge = meta.meta_bp_v3_hop;
        hdr.recoveryPath[3].bos = 0;
        hdr.recoveryPath[3].edge = meta.meta_bp_v4_hop;
        hdr.recoveryPath[4].bos = meta.cur_bos;
        hdr.recoveryPath[4].edge = meta.meta_bp_v5_hop;
    }
    action add_header_fault_6(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(6);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[2].setValid();
        hdr.recoveryPath[3].setValid();
        hdr.recoveryPath[4].setValid();
        hdr.recoveryPath[5].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 0;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
        hdr.recoveryPath[2].bos = 0;
        hdr.recoveryPath[2].edge = meta.meta_bp_v3_hop;
        hdr.recoveryPath[3].bos = 0;
        hdr.recoveryPath[3].edge = meta.meta_bp_v4_hop;
        hdr.recoveryPath[4].bos = 0;
        hdr.recoveryPath[4].edge = meta.meta_bp_v5_hop;
        hdr.recoveryPath[5].bos = meta.cur_bos;
        hdr.recoveryPath[5].edge = meta.meta_bp_v6_hop;
    }
    action add_header_fault_7(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(7);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[2].setValid();
        hdr.recoveryPath[3].setValid();
        hdr.recoveryPath[4].setValid();
        hdr.recoveryPath[5].setValid();
        hdr.recoveryPath[6].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 0;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
        hdr.recoveryPath[2].bos = 0;
        hdr.recoveryPath[2].edge = meta.meta_bp_v3_hop;
        hdr.recoveryPath[3].bos = 0;
        hdr.recoveryPath[3].edge = meta.meta_bp_v4_hop;
        hdr.recoveryPath[4].bos = 0;
        hdr.recoveryPath[4].edge = meta.meta_bp_v5_hop;
        hdr.recoveryPath[5].bos = 0;
        hdr.recoveryPath[5].edge = meta.meta_bp_v6_hop;
        hdr.recoveryPath[6].bos = meta.cur_bos;
        hdr.recoveryPath[6].edge = meta.meta_bp_v7_hop;
    }
    action add_header_fault_8(){
        hdr.ethernet.etherType = TYPE_RECOVERYPATH;
        hdr.recoveryPath.push_front(8);
        hdr.recoveryPath[0].setValid();
        hdr.recoveryPath[1].setValid();
        hdr.recoveryPath[2].setValid();
        hdr.recoveryPath[3].setValid();
        hdr.recoveryPath[4].setValid();
        hdr.recoveryPath[5].setValid();
        hdr.recoveryPath[6].setValid();
        hdr.recoveryPath[7].setValid();
        hdr.recoveryPath[0].bos = 0;
        hdr.recoveryPath[0].edge = meta.meta_bp_v1_hop;
        hdr.recoveryPath[1].bos = 0;
        hdr.recoveryPath[1].edge = meta.meta_bp_v2_hop;
        hdr.recoveryPath[2].bos = 0;
        hdr.recoveryPath[2].edge = meta.meta_bp_v3_hop;
        hdr.recoveryPath[3].bos = 0;
        hdr.recoveryPath[3].edge = meta.meta_bp_v4_hop;
        hdr.recoveryPath[4].bos = 0;
        hdr.recoveryPath[4].edge = meta.meta_bp_v5_hop;
        hdr.recoveryPath[5].bos = 0;
        hdr.recoveryPath[5].edge = meta.meta_bp_v6_hop;
        hdr.recoveryPath[6].bos = 0;
        hdr.recoveryPath[6].edge = meta.meta_bp_v7_hop;
        hdr.recoveryPath[7].bos = meta.cur_bos;
        hdr.recoveryPath[7].edge = meta.meta_bp_v8_hop;
    }
        
    apply {
        if (hdr.ipv4.isValid() && !hdr.recoveryPath[0].isValid()) {
            // Process only non-tunneled IPv4 packets
            ipv4_lpm.apply();
            //1 for failover
            if(meta.out_port_status == 1){
                port_backup_path.apply();
                if(meta.port_backup_length == 1){
                    add_header_normal_1();
                }
                else if(meta.port_backup_length == 2){
                    add_header_normal_2();
                }
                else if(meta.port_backup_length == 3){
                    add_header_normal_3();
                }
                else if(meta.port_backup_length == 4){
                    add_header_normal_4();
                }
                else if(meta.port_backup_length == 5){
                    add_header_normal_5();
                }
                else if(meta.port_backup_length == 6){
                    add_header_normal_6();
                }
                else if(meta.port_backup_length == 7){
                    add_header_normal_7();
                }
                else if(meta.port_backup_length == 8){
                    add_header_normal_8();
                }
            }
        }


        if (hdr.recoveryPath[0].isValid()) {
            // process recovery packet
            if (hdr.recoveryPath[0].bos == 1){
                recoveryPath_finish();
            }
            recoveryPath_nhop();
            edge_to_port.apply();
            if(meta.out_port_status == 1){
                //如果在故障恢复的过程中同样碰到了故障，则需要继续增加头部，
                //但是不需要设置bos为1，除非目前的bos为1
                //并且，这里需要从入口处再跑一次，也就是recycle一下！
                meta.need_recycle = 1;
                port_backup_path_fault.apply();
                if(meta.port_backup_length == 1){
                    add_header_fault_1();
                }
                else if(meta.port_backup_length == 2){
                    add_header_fault_2();
                }
                else if(meta.port_backup_length == 3){
                    add_header_fault_3();
                }
                else if(meta.port_backup_length == 4){
                    add_header_fault_4();
                }
                else if(meta.port_backup_length == 5){
                    add_header_fault_5();
                }
                else if(meta.port_backup_length == 6){
                    add_header_fault_6();
                }
                else if(meta.port_backup_length == 7){
                    add_header_fault_7();
                }
                else if(meta.port_backup_length == 8){
                    add_header_fault_8();
                }
            }
        }
        //if we are doing failover, do we need to decrease ttl?
        if(hdr.ipv4.isValid()){
            update_ttl();
        }

        //comment for test
        //port_to_mac.apply();//update mac
    }
}


control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply { 
        if(meta.need_recycle == 1) {
            recirculate(standard_metadata);
        }
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
    apply {  }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/
control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.recoveryPath);
        packet.emit(hdr.ipv4);
    }
}
/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;