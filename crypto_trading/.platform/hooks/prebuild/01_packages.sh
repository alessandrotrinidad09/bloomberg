#!/bin/bash
# .platform/hooks/prebuild/01_install_packages.sh
# Instala dependencias necesarias para mysqlclient y cryptography
dnf install -y mariadb-connector-c-devel python3-devel gcc gcc-c++ make pkgconfig libffi-devel openssl-devel

# Exporta variables para mysqlclient
export MYSQLCLIENT_CFLAGS="-I/usr/include/mariadb"
export MYSQLCLIENT_LDFLAGS="-L/usr/lib64/mariadb -lmariadb"

# Evita errores con cryptography en Python 3.13
export CRYPTOGRAPHY_DONT_BUILD_RUST=1
