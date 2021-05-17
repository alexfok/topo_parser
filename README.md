# TODO
# Step 2 - Create links and systems dictionaries
# Step 3 - Push links and systems dictionaries to Redis
# Step 4 - Draw topology graph?
# Step 5 - play with json formats - original, short, etc

docker pull redis
docker run --name topo-redis -d redis redis-server 
docker run -it --rm redis redis-cli -h topo-redis
#docker run -v /myredis/conf:/usr/local/etc/redis --name myredis redis redis-server /usr/local/etc/redis/redis.conf
vi /etc/redis.conf
systemctl start redis.service
systemctl enable redis.service
redis-cli -h 10.210.8.142 ping

# Device types
vendid=0x2c9
devid=0xcf09
sysimgguid=0x2c90000020cfb
caguid=0x2c90000020cf9
Ca 1 "H-0002c90000020cf9" # "Mellanox Technologies Aggregation Node"
[1](2c90000020cfa) 	"S-0002c90000020cfc"[41]		# lid 40737 lmc 0 "MF0;L0_R05_B16_I20:MQM8700/U1" lid 35908 4xHDR

vendid=0x2c9
devid=0x5a44
sysimgguid=0x2c90000017e00
caguid=0x2c90000017dfd
Ca	2 "H-0002c90000017dfd"		# "H_32000 HCA-1 (Mellanox HCA)"
[1](2c90000017dfe) 	"S-0002c90000020cfc"[20]		# lid 36214 lmc 0 "MF0;L0_R05_B16_I20:MQM8700/U1" lid 35908 4xHDR
