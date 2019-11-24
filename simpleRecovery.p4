#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_RECOVERYPATH = 0x1212;
const bit<16> TYPE_IPV4 = 0x800;
#define MAX_HOPS 8;
#define MAX_PORTS 128;
/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}
//recover
header recoveryPath_t {
    bit<1>    bos;
    bit<7>   port;
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
    bit<7>  start_port;
    bit<1>  out_port_status;
    bit<3>  port_backup_length; 
    bit<7>  meta_bp_v1_hop;
    bit<7>  meta_bp_v2_hop;
    bit<7>  meta_bp_v3_hop;
    bit<7>  meta_bp_v4_hop;
    bit<7>  meta_bp_v5_hop;
    bit<7>  meta_bp_v6_hop;
    bit<7>  meta_bp_v7_hop;
    bit<7>  meta_bp_v8_hop;
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
                inout metadata_t meta,
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
        action = {
            try_ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    action copy_path(backup_length_t length,bp_v1_hop_t v1,bp_v2_hop_t v2,bp_v3_hop_t v3,bp_v4_hop_t v4,bp_v5_hop_t v5,bp_v6_hop_t v6,bp_v7_hop_t v7,bp_v8_hop_t v8){
            meta.port_backup_length=length;
            meta.meta_bp_v1_hop=v1;
            meta.meta_bp_v2_hop=v2;
            meta.meta_bp_v3_hop=v3;
            meta.meta_bp_v5_hop=v4;
            meta.meta_bp_v6_hop=v5;
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

    action update_mac_addr(macAddr_t dstAddr) {
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
    }
    table port_to_mac [
        key = {
            standard_metadata.egress_spec: exact;
        }
        action = {
            update_mac_addr;
        }
    ]

    action recoveryPath_finish() {
        hdr.ethernet.etherType = TYPE_IPV4;
    }
    action update_ttl(){
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }
    action recoveryPath_nhop() {
        standard_metadata.egress_spec = (bit<9>) hdr.recoveryPath[0].port;
        hdr.srcRoutes.pop_front(1);
    }
    action update_1_length(){
        hdr.recoveryPath.pushfront(1);
        hdr.srecoveryPath[0].bos == 1;
        hdr.srecoveryPath[0].port == meta.meta_bp_v1_hop;
    }
    action update_2_length(){
        hdr.recoveryPath.pushfront(2);
        hdr.srecoveryPath[0].bos == 0;
        hdr.srecoveryPath[0].port == meta.meta_bp_v1_hop;
        hdr.srecoveryPath[1].bos == 1;
        hdr.srecoveryPath[1].port == meta.meta_bp_v2_hop;
    }
    action update_3_length(){
        hdr.recoveryPath.pushfront(3);
        hdr.srecoveryPath[0].bos == 0;
        hdr.srecoveryPath[0].port == meta.meta_bp_v1_hop;
        hdr.srecoveryPath[1].bos == 0;
        hdr.srecoveryPath[1].port == meta.meta_bp_v2_hop;
        hdr.srecoveryPath[2].bos == 0;
        hdr.srecoveryPath[2].port == meta.meta_bp_v3_hop;
    }
    action update_4_length(){
        hdr.recoveryPath.pushfront(4);
        hdr.srecoveryPath[0].bos == 0;
        hdr.srecoveryPath[0].port == meta.meta_bp_v1_hop;
        hdr.srecoveryPath[1].bos == 0;
        hdr.srecoveryPath[1].port == meta.meta_bp_v2_hop;
        hdr.srecoveryPath[2].bos == 0;
        hdr.srecoveryPath[2].port == meta.meta_bp_v3_hop;
        hdr.srecoveryPath[3].bos == 1;
        hdr.srecoveryPath[3].port == meta.meta_bp_v4_hop;
    }
    action update_5_length(){
        hdr.recoveryPath.pushfront(5);
        hdr.srecoveryPath[0].bos == 0;
        hdr.srecoveryPath[0].port == meta.meta_bp_v1_hop;
        hdr.srecoveryPath[1].bos == 0;
        hdr.srecoveryPath[1].port == meta.meta_bp_v2_hop;
        hdr.srecoveryPath[2].bos == 0;
        hdr.srecoveryPath[2].port == meta.meta_bp_v3_hop;
        hdr.srecoveryPath[3].bos == 0;
        hdr.srecoveryPath[3].port == meta.meta_bp_v4_hop;
        hdr.srecoveryPath[4].bos == 1;
        hdr.srecoveryPath[4].port == meta.meta_bp_v5_hop;
    }
    action update_6_length(){
        hdr.recoveryPath.pushfront(6);
        hdr.srecoveryPath[0].bos == 0;
        hdr.srecoveryPath[0].port == meta.meta_bp_v1_hop;
        hdr.srecoveryPath[1].bos == 0;
        hdr.srecoveryPath[1].port == meta.meta_bp_v2_hop;
        hdr.srecoveryPath[2].bos == 0;
        hdr.srecoveryPath[2].port == meta.meta_bp_v3_hop;
        hdr.srecoveryPath[3].bos == 0;
        hdr.srecoveryPath[3].port == meta.meta_bp_v4_hop;
        hdr.srecoveryPath[4].bos == 0;
        hdr.srecoveryPath[4].port == meta.meta_bp_v5_hop;
        hdr.srecoveryPath[5].bos == 1;
        hdr.srecoveryPath[5].port == meta.meta_bp_v6_hop;
    }
    action update_7_length(){
        hdr.recoveryPath.pushfront(7);
        hdr.srecoveryPath[0].bos == 0;
        hdr.srecoveryPath[0].port == meta.meta_bp_v1_hop;
        hdr.srecoveryPath[1].bos == 0;
        hdr.srecoveryPath[1].port == meta.meta_bp_v2_hop;
        hdr.srecoveryPath[2].bos == 0;
        hdr.srecoveryPath[2].port == meta.meta_bp_v3_hop;
        hdr.srecoveryPath[3].bos == 0;
        hdr.srecoveryPath[3].port == meta.meta_bp_v4_hop;
        hdr.srecoveryPath[4].bos == 0;
        hdr.srecoveryPath[4].port == meta.meta_bp_v5_hop;
        hdr.srecoveryPath[5].bos == 0;
        hdr.srecoveryPath[5].port == meta.meta_bp_v6_hop;
        hdr.srecoveryPath[6].bos == 1;
        hdr.srecoveryPath[6].port == meta.meta_bp_v7_hop;
    }
    action update_8_length(){
        hdr.recoveryPath.pushfront(8);
        hdr.srecoveryPath[0].bos == 0;
        hdr.srecoveryPath[0].port == meta.meta_bp_v1_hop;
        hdr.srecoveryPath[1].bos == 0;
        hdr.srecoveryPath[1].port == meta.meta_bp_v2_hop;
        hdr.srecoveryPath[2].bos == 0;
        hdr.srecoveryPath[2].port == meta.meta_bp_v3_hop;
        hdr.srecoveryPath[3].bos == 0;
        hdr.srecoveryPath[3].port == meta.meta_bp_v4_hop;
        hdr.srecoveryPath[4].bos == 0;
        hdr.srecoveryPath[4].port == meta.meta_bp_v5_hop;
        hdr.srecoveryPath[5].bos == 0;
        hdr.srecoveryPath[5].port == meta.meta_bp_v6_hop;
        hdr.srecoveryPath[6].bos == 0;
        hdr.srecoveryPath[6].port == meta.meta_bp_v7_hop;
        hdr.srecoveryPath[7].bos == 1;
        hdr.srecoveryPath[7].port == meta.meta_bp_v8_hop;
    }
        
    apply {
        if (hdr.ipv4.isValid() && !hdr.recoveryPath.isValid()) {
            // Process only non-tunneled IPv4 packets
            ipv4_lpm.apply();
            //1 for failover
            if(meta.out_port_status == 1){
                port_backup_path.apply();
                if(meta.port_backup_length == 1){
                    update_1_length();
                }
                if(meta.port_backup_length == 2){
                    update_2_length();
                }
                if(meta.port_backup_length == 3){
                    update_3_length();
                }
                if(meta.port_backup_length == 4){
                    update_4_length();
                }
                if(meta.port_backup_length == 5){
                    update_5_length();
                }
                if(meta.port_backup_length == 6){
                    update_6_length();
                }
                if(meta.port_backup_length == 7){
                    update_7_length();
                }
                if(meta.port_backup_length == 8){
                    update_8_length();
                }
            }
        }


        if (hdr.recoveryPath[0].isValid()) {
            if (hdr.srecoveryPath[0].bos == 1){
                recoveryPath_finish();
            }
            // process tunneled packets
            recoveryPath_nhop();
        }
        //if we are doing failover, do we need to decrease ttl?
        if(hdr.ipv4.isValid()){
            update_ttl;
        }
        
        port_to_mac.apply();//update mac
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