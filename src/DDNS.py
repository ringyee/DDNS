'''
DDNS 主程序 使用阿里云的SDK发起请求
Created By Martin Huang on 2018/5/20
修改记录：
2018/5/20 => 第一版本
2018/5/26 => 增加异常处理、Requst使用单例模式，略有优化
2018/5/29 => 增加网络连通性检测，只有联通时才进行操作，否则等待
2018/6/10 => 使用配置文件存储配置，避免代码内部修改(需要注意Python模块相互引用问题)
2018/9/24 => 修改失败提示信息
'''
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.acs_exception.exceptions import ClientException
from Utils import Utils
import time
import argparse

def DDNS(use_v6):
    domain = Utils.getConfigJson().get('First-level-domain')
    subDomain = Utils.getConfigJson().get('Second-level-domain')
    client = Utils.getAcsClient()
    recordId = Utils.getRecordId(subDomain)
    if use_v6:
        ip = Utils.getRealIPv6()
        type = 'AAAA'
    else:
        ip = Utils.getRealIP()
        type = 'A'
    print({'type': type, 'ip':ip, 'domain':subDomain+'.'+domain})

    needToUpdate = True
    try:
        f = open('.ip', 'r+')
        line = f.readline()
        line = line.strip()
        if line == ip:
            needToUpdate = False
            print('No need to update!')
        f.close();
    except FileNotFoundError:
        pass

    if needToUpdate:
        request = Utils.getCommonRequest()
        request.set_domain('alidns.aliyuncs.com')
        request.set_version('2015-01-09')
        request.set_action_name('UpdateDomainRecord')
        request.add_query_param('RecordId', recordId)
        request.add_query_param('RR', subDomain)
        request.add_query_param('Type', type)
        request.add_query_param('Value', ip)
        response = client.do_action_with_exception(request)

        f = open('.ip', 'w')
        f.write(ip)
        f.close();

        return response

    return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='DDNS')
    parser.add_argument('-6', '--ipv6', nargs='*', default=False)
    args = parser.parse_args()
    isipv6 = isinstance(args.ipv6, list)

    try:
        while not Utils.isOnline():
            time.sleep(3)
            continue
        result = DDNS(isipv6)
        print("成功！")
    except (ServerException,ClientException) as reason:
        print("失败！原因为")
        print(reason.get_error_msg())
        if 'already exists' in reason.get_error_msg():
            if isipv6:
                ip = Utils.getRealIPv6()
            else:
                ip = Utils.getRealIP()
                
            f = open('.ip', 'w')
            f.write(ip)
            f.close();
