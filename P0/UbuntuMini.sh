#!/bin/bash

if [ $# -ne 1 ];
	then echo "Debes indicar como argumento el nº de máquina virtual: 1, 2, ó 3."
	exit
fi

if [ ! $1 = 1 ]; then
	if [ ! $1 = 2 ]; then
		if [ ! $1 = 3 ]; then
    			echo "Debes indicar como argumento el nº de máquina virtual: 1, 2, ó 3."
			exit 
		fi
	fi
fi

num_vm=$1

VMimage="https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.ova"
VMname="si2vm$num_vm"
VMhostname="si2-ubuntu-vm-$num_vm"
VMusername="si2"
VMtimezone=`cat /etc/timezone`
VMlocale=`localectl | grep LANG | cut -f2 -d:`
VMkeyboard=`localectl | grep "X11 Layout" | cut -f2 -d:`
VMdir=$HOME"/VirtualBox VMs"

port_ssh_host_pc=$num_vm\2022
port_gunicorn_web_host_pc=$num_vm\8000
port_web_host_pc=$num_vm\8080
port_posgresql_host_pc=$num_vm\5432
port_rabbitmq_host_pc=$num_vm\5672

### DO NOT TOUCH AFTER THIS LINE (unless you know what you are doing)

# Prepare vm-config.sh script to be run on the new VM

echo "Prepare vm-config.sh script"
echo '#!/bin/bash' > vm-config.sh
echo "VMhostname=\"$VMhostname\"" >> vm-config.sh
echo "VMusername=\"$VMusername\"" >> vm-config.sh
echo "VMtimezone=\""`cat /etc/timezone`"\"" >> vm-config.sh
echo "VMlocale=\""`localectl | grep LANG | cut -f2 -d:`"\"" >> vm-config.sh
echo "VMkeyboard=\""`localectl | grep "X11 Layout" | cut -f2 -d:`"\"" >> vm-config.sh

cat > requirements.txt << "EOF"
asgiref==3.8.1
beautifulsoup4==4.12.3
certifi==2024.8.30
charset-normalizer==3.4.0
dj-database-url==2.2.0
Django==4.2.13
django-modern-rpc==1.0.3
djangorestframework==3.15.2
Faker==30.8.0
flake8==6.1.0
google==3.0.0
grpc-django==1.0.0
grpcio==1.67.1
grpcio-tools==1.67.1
gunicorn==20.1.0
idna==3.10
protobuf==5.28.3
psycopg2-binary==2.9.9
python-dateutil==2.9.0.post0
python-dotenv==0.21.0
requests==2.32.3
six==1.16.0
soupsieve==2.6
sqlparse==0.5.1
typing_extensions==4.12.2
urllib3==2.2.3
whitenoise==6.7.0
EOF

cat >> vm-config.sh <<"EOF"
# Define colors
LGREEN='\033[1;32m'
NC='\033[0m' # No Color

echo -e "${LGREEN}*** Now running on $HOSTNAME${NC}"
echo -e "${LGREEN}*** Fixing /etc/hosts${NC}"
if ! grep $VMhostname -q /etc/hosts
then sed -i".bak" "/127\.0\.0\.1/ s/$/ ${VMhostname}/" /etc/hosts
fi

echo -e "${LGREEN}*** Configuring localization for "$HOSTNAME"....${NC}"
timedatectl set-timezone $VMtimezone
localectl set-locale $VMlocale
localectl set-keymap $VMkeyboard
loadkeys  $VMkeyboard
echo -e "sudo loadkeys $VMkeyboard" > /home/$VMusername/.bashrc

echo -e "${LGREEN}*** Configuring ssh for "$HOSTNAME"....${NC}"
cat /etc/ssh/sshd_config | sed s/"#PasswordAuthentication yes"/"PasswordAuthentication yes\nChallengeResponseAuthentication yes"/g > /tmp/config 
sudo mv /tmp/config /etc/ssh/sshd_config
sudo /etc/init.d/ssh restart

echo -e "${LGREEN}*** Set password for $VMusername on "$HOSTNAME"....${NC}"
passwd $VMusername

echo -e "${LGREEN}*** Updating packages...${NC}"
apt update
apt -y upgrade

echo -e "${LGREEN}*** Installing Posgresql ...${NC}"
apt -y install postgresql tasksel
echo -e "${LGREEN}*** Installing Net-tools and nmon...${NC}"
apt -y install net-tools nmon tasksel
echo -e "${LGREEN}*** Installing Apache2...${NC}"
apt -y install apache2 tasksel
echo -e "${LGREEN}*** Installing rabbitmq...${NC}"
apt -y install rabbitmq-server tasksel
echo -e "${LGREEN}*** Installing python and pip ...${NC}"
apt -y install python3-venv python3-pip tasksel

sudo -u si2 python3 -m venv /home/si2/venv
echo -e "export PATH=/home/si2/venv/bin:$PATH" >> /home/$VMusername/.bashrc

echo -e "${LGREEN}*** Installing python package requirements ...${NC}"
sudo -u si2 /home/si2/venv/bin/pip install -r /tmp/requirements.txt

echo -e "${LGREEN}*** Configuring Postgresql...${NC}"
sudo -u postgres createuser -e alumnodb -s
echo "local all     alumnodb           trust" > /tmp/pg_hba.conf
echo "host     all     alumnodb        127.0.0.1/32       trust" >> /tmp/pg_hba.conf
echo "host     all     alumnodb        0.0.0.0/0       trust" >> /tmp/pg_hba.conf
cat `find /etc -name pg_hba.conf 2> /dev/null` >> /tmp/pg_hba.conf
mv /tmp/pg_hba.conf `find /etc -name pg_hba.conf 2> /dev/null`
echo "listen_addresses = '*'" > /tmp/postgres.conf
cat /tmp/postgres.conf >> `find /etc -name postgresql.conf 2> /dev/null`
rm /tmp/postgres.conf

# echo -e "${LGREEN}*** Installing git ...${NC}"
# apt -y install git

echo -e "${LGREEN}*** Consider rebooting the VM before using${NC}"


EOF

# prepare the tools. Esto debe estar instalado. Pedirlo en los laboratoiros y quitarlo de aquí.
#sudo apt-get install cloud-image-utils

imgFile=`basename $VMimage`
echo $imgFile

# get the image
if [ ! -e $imgFile ]
then wget $VMimage
fi

VBoxManage import $imgFile --vsys 0 --vmname $VMname
VBoxManage modifyvm $VMname --memory 1500					# Set 1.5G of RAM
VBoxManage modifyvm $VMname --cpus 1 					# Set 1 CPU
VBoxManage modifyvm $VMname --nic1 nat					# Set networking as NAT
VBoxManage modifyvm $VMname --natpf1 ,tcp,,$port_ssh_host_pc,,22     # Enable port forwarding for ssh
VBoxManage modifyvm $VMname --natpf1 ,tcp,,$port_gunicorn_web_host_pc,,8000     # Enable port forwarding for gunicorn web
VBoxManage modifyvm $VMname --natpf1 ,tcp,,$port_web_host_pc,,80     # Enable port forwarding for apache2
VBoxManage modifyvm $VMname --natpf1 ,tcp,,$port_posgresql_host_pc,,5432 # Enable port forwarding for posgresql
VBoxManage modifyvm $VMname --natpf1 ,tcp,,$port_rabbitmq_host_pc,,5672 # Enable port forwarding for rabbitmq
VBoxManage storagectl $VMname --name Floppy --remove    # Remove floppy driver

# Create the configuration DVD
cat > meta-data <<EOF
instance-id: ubuntu
local-hostname: $VMhostname
EOF
cat > user-data <<EOF
#cloud-config
users:
  - name: $VMusername
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
    shell: /bin/bash
EOF
echo "    ssh_authorized_keys: " >> user-data
for f in ~/.ssh/*.pub
do 
	echo -n "      - " >> user-data
	cat $f >> user-data
done
# Password initialization not working... why?
#echo -n "    passwd: " >> user-data
#cat >> user-data <<"EOF"
#...input from mkpasswd here
#EOF
cloud-localds ciconf.iso user-data meta-data 
rm user-data meta-data

# Mount the configuration disk

VBoxManage storageattach $VMname --storagectl IDE --port 0 --device 0 --type dvddrive --medium ciconf.iso

VBoxManage startvm $VMname

echo "Type 'return' on *this* terminal when the login prompt appears on the VM terminal..." 
read

ssh-keygen -f "/home/$USER/.ssh/known_hosts" -R "[localhost]:$port_ssh_host_pc"
echo "Transfer the vmconfig.sh script"
scp -P $port_ssh_host_pc vm-config.sh $VMusername@localhost:/tmp/
scp -P $port_ssh_host_pc requirements.txt $VMusername@localhost:/tmp/
echo "Running the script on the VM"
ssh -tt -p $port_ssh_host_pc $VMusername@localhost "sudo bash /tmp/vm-config.sh"
