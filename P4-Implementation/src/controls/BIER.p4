control BIER(inout header_t hdr, inout ingress_metadata_t ig_md, inout ingress_intrinsic_metadata_for_tm_t ig_tm_md, inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md) {

    action clone() {
    }

    action mc_forward(bierBitmask fbm, bit<16> mgrp_id) {
        // save new bier bs for clone
        hdr.bier.bs = hdr.bier.bs & fbm; // new bier bs for outgoing packet
        ig_tm_md.mcast_grp_a = mgrp_id;
    }

    // port is not part of cluster
    // iterative processing
    action forward(bierBitmask fbm, PortId_t e_port) {
        // save new bier bs for clone
        hdr.bier.bs = hdr.bier.bs & fbm; // new bier bs for outgoing packet
        ig_tm_md.ucast_egress_port = e_port;
    }

    action set_cluster(bierBitmask fbm, bit<10> cluster_id) {
        ig_md.cluster_id = cluster_id;
        ig_md.temp_bs = hdr.bier.bs & fbm;
    }

    table cluster {
      key = {
        hdr.bier.bs: ternary;
      }
      actions = {
        set_cluster;
      }
      size = 20000;
    }


    table bift {
        key = {
            ig_md.cluster_id: exact;
            ig_md.temp_bs: ternary;
        }
        actions = {
            mc_forward;
            forward;
        }
        size = 12000;
    }

    table default_bift { 
      key = {
        hdr.bier.bs: ternary;
      }
      actions = {
        forward;
      }
    }

    // test on empty bs
    action nop() {}

    table reset_clone {
      key = {
        hdr.bier_md.bs: exact;
      }
      actions = {
        nop;
      }
      size = 100;
    }

    table reset_clone_2 {
      key = {
        hdr.bier_md.bs: exact;
      }
      actions = {
        nop;
      }
      size = 100;
    }

    table reset_clone_3 {
      key = {
        hdr.bier_md.bs: exact;
      }
      actions = {
        nop;
      }
      size = 100;
    }



    apply {
      ig_md.mirror_session = 0;
      hdr.bier_md.setValid();
      hdr.bier_md.bs = hdr.bier.bs;
      if(!reset_clone.apply().hit) {
        if(cluster.apply().hit) {
            if(bift.apply().hit) {
              // test if bs is empty
              hdr.bier_md.bs = hdr.bier_md.bs & ~hdr.bier.bs;

              if(!reset_clone_2.apply().hit) {
                ig_dprsr_md.mirror_type = 1; // set clone flag, will be cloned to recirculation port
                ig_md.mirror_session = 1000;
              }
            }
        }
        else {
          if(default_bift.apply().hit) {
              hdr.bier_md.bs = hdr.bier_md.bs & ~hdr.bier.bs;

              if(!reset_clone_3.apply().hit) {
                ig_dprsr_md.mirror_type = 1; // set clone flag, will be cloned to recirculation port
                ig_md.mirror_session = 1000;
              }
 
          }
        }
      }
    }
}
