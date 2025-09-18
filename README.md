# MudHunter
Internet-scale DNS cache snooping for domain activity estimation using CAIDA Ark vantage points.

## Overview
MudHunter centrally orchestrates parallel RD=0 DNS probes from CAIDA Ark vantage points to major public resolvers and aggregates TTL observations by {resolver, PoP}. It requires **access to CAIDA Ark**.

- Ark access: apply here → https://www.caida.org/projects/ark/programming/
- Once approved, you’ll run MudHunter from an Ark login/controller host with access to the scamper controller mux (e.g., `/run/ark/mux`).

## Requirements
- Linux (tested on Ubuntu)
- Python 3.10+
- Access to a CAIDA Ark host with `scamper` controller mux (e.g., `/run/ark/mux`)
- (Optional) `virtualenv` for isolation

> Note: You do **not** deploy code on Ark nodes; the controller talks to them via scamper’s controller interface.

## how to run
```bash
python3.10 mudhunter.py <ark_mux_path> <domains.txt> <output_dir> <resolver1> <resolver2> <resolver3> <resolver4>

