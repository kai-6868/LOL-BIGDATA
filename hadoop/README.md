# Hadoop Bin Directory

This directory serves as a dummy `HADOOP_HOME` for PySpark on Windows.

## Purpose

PySpark on Windows requires `HADOOP_HOME` to be set, even when not using HDFS locally. This directory provides a portable solution that works across different machines without requiring system-wide Hadoop installation.

## How it works

1. The `pyspark_etl.py` script automatically:
   - Detects the project root directory
   - Sets `HADOOP_HOME` to `<project>/hadoop`
   - Creates `hadoop/bin` if it doesn't exist

2. This approach is **portable** - works on any machine without configuration

3. The `bin/winutils.exe` file is a dummy placeholder to suppress warnings

## Benefits

- ✅ No system-wide Hadoop installation needed
- ✅ Works on any Windows machine
- ✅ Project is self-contained
- ✅ No manual configuration required
- ✅ Version control friendly

## Note

For actual HDFS operations, the code uses Docker containers (namenode/datanode), not this local Hadoop installation.
