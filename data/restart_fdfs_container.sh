STORAGE_NAME=storage
STORAGE_DIR=/var/fdfs/storage
TRACKER_NAME=tracker
TRACKER_DIR=/var/fdfs/tracker
DATA_FILE=./data.tar.gz
FDFS_IMAGE=./fastdfs_docker.tar
YOUR_IP=$1



check() {
    if [ ! -f ${DATA_FILE} ];then
        echo "未检测到data.tar.gz备份文件，请把该文件放入当前目录！"
        exit
    fi

    if [ ! ${YOUR_IP} ];then
        echo "请求输入您的ip: \"./restart_fdfs_container.sh <您的ip>\""
        exit
    fi
}

load_image(){
    sudo docker image load < ${FDFS_IMAGE}
}

delete_data() {
    if [ ! -d /var/fdfs ];then
       sudo mkdir /var/fdfs
    fi

    if [ -d ${TRACKER_DIR} ];then 
        echo "删除tracker残余数据..."
        sudo rm -rf ${TRACKER_DIR}/*
    else
        echo "新建tracker映射目录"
        sudo mkdir ${TRACKER_DIR}
    fi

    if [ -d ${STORAGE_DIR} ];then 
        echo "删除storage残余数据..."
        sudo rm -rf ${STORAGE_DIR}/*
    else
        echo "新建storage映射目录"
        sudo mkdir ${STORAGE_DIR}
    fi
}

delete_container() {
    echo "清除原有容器..."
    docker container rm -f ${STORAGE_NAME}
    docker container rm -f ${TRACKER_NAME}
}

create_container() {
    echo "构建新容器..."

    sudo docker run -dit --name=tracker --network=host -v /var/fdfs/tracker:/var/fdfs delron/fastdfs tracker

    sudo docker run -dti --name=storage --network=host -e TRACKER_SERVER=${YOUR_IP}:22122 -v /var/fdfs/storage:/var/fdfs delron/fastdfs storage

}


tar_data() {
    echo "解压商品数据..."
    sudo tar -zxf ${DATA_FILE} -C ${STORAGE_DIR}
}


main() {
    check
    # load_image
    delete_data
    delete_container
    create_container
    tar_data
    docker container ls -a
}


main



