#!/usr/bin/env bash
# Run lyra from anywhere, no need to cd first.
cd "$(dirname "$0")" && python3 -m lyra "$@"
