/*******************************************************************************
 * BAREFOOT NETWORKS CONFIDENTIAL & PROPRIETARY
 *
 * Copyright (c) 2018-2019 Barefoot Networks, Inc.
 * All Rights Reserved.
 *
 * NOTICE: All information contained herein is, and remains the property of
 * Barefoot Networks, Inc. and its suppliers, if any. The intellectual and
 * technical concepts contained herein are proprietary to Barefoot Networks,
 * Inc.
 * and its suppliers and may be covered by U.S. and Foreign Patents, patents in
 * process, and are protected by trade secret or copyright law.
 * Dissemination of this information or reproduction of this material is
 * strictly forbidden unless prior written permission is obtained from
 * Barefoot Networks, Inc.
 *
 * No warranty, explicit or implicit is provided, unless granted under a
 * written agreement with Barefoot Networks, Inc.
 *
 *
 ******************************************************************************/

#ifndef _HEADERS_
#define _HEADERS_

typedef bit<48> mac_addr_t;
typedef bit<32> ipv4_addr_t;
typedef bit<128> bierBitmask;
typedef bit<16> ether_type_t;
const ether_type_t ETHERTYPE_IPV4 = 0x800;
const ether_type_t TYPE_ARP = 0x0806;
const ether_type_t ETHERTYPE_BIER = 0xBB00;
const ether_type_t ETHERTYPE_BIER_MD = 0xBB02;
const PortId_t CPU_PORT = 192;

header ethernet_h {
    mac_addr_t dst_addr;
    mac_addr_t src_addr;
    bit<16> ether_type;
}

header ipv4_t {
    bit<4> version;
    bit<4> ihl;
    bit<8> diffserv;
    bit<16> total_len;
    bit<16> identification;
    bit<3> flags;
    bit<13> frag_offset;
    bit<8> ttl;
    bit<8> protocol;
    bit<16> hdr_checksum;
    ipv4_addr_t src_addr;
    ipv4_addr_t dst_addr;
}


header arp_t {
    bit<16> hardwareaddr_t;
    bit<16> protoaddr_t;
    bit<8> hardwareaddr_s;
    bit<8> protoaddr_s;
    bit<16> op;
    mac_addr_t src_mac_addr;
    ipv4_addr_t src_ip_addr;
    mac_addr_t dst_mac_addr;
    ipv4_addr_t dst_ip_addr;
}

header bier_t {
    bierBitmask bs;
    bit<16> proto;
}

header bier_md_t {
    bierBitmask bs;
}

struct header_t {
    ethernet_h ethernet;
    arp_t	arp;
    ipv4_t ipv4;
    bier_t bier;
    bier_md_t bier_md;
    ipv4_t ipv4_inner;
}


struct ingress_metadata_t {
    bool checksum_err;
    bit<10> mirror_session;
    bit<20> random_header_index;
    bit<32> port_down_bit;
    bierBitmask temp_bs;
    bit<10> cluster_id;
}

struct egress_metadata_t {
}


#endif /* _HEADERS_ */
