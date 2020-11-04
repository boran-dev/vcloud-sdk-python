# coding:utf-8

from __future__ import print_function
import os
import threading
import time
from zlib import crc32
from ttvcloud.ApiInfo import ApiInfo
from ttvcloud.Credentials import Credentials
from ttvcloud.ServiceInfo import ServiceInfo
from ttvcloud.base.Service import Service
from ttvcloud.const.Const import *
from ttvcloud.Policy import *
from ttvcloud.util.Util import *
from google.protobuf.json_format import *
from ttvcloud.models.vod.request.request_vod_pb2 import *
from ttvcloud.models.vod.response.response_vod_pb2 import *


class VodService(Service):
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not hasattr(VodService, "_instance"):
            with VodService._instance_lock:
                if not hasattr(VodService, "_instance"):
                    VodService._instance = object.__new__(cls)
        return VodService._instance

    def __init__(self, region='cn-north-1'):
        self.service_info = VodService.get_service_info(region)
        self.api_info = VodService.get_api_info()
        self.domain_cache = {}
        self.fallback_domain_weights = {}
        self.update_interval = 10
        self.lock = threading.Lock()
        super(VodService, self).__init__(self.service_info, self.api_info)

    # TODO 测试完毕修改回来
    @staticmethod
    def get_service_info(region):
        service_info_map = {
            # 'cn-north-1': ServiceInfo("vod.bytedanceapi.com", {'Accept': 'application/json'},
            #                           Credentials('', '', 'vod', 'cn-north-1'), 5, 5),
            'cn-north-1': ServiceInfo("staging-openapi-boe.byted.org", {'Accept': 'application/json'},
                                      Credentials('', '', 'vod', 'cn-north-1'), 5, 5),
            'ap-singapore-1': ServiceInfo("vod.ap-singapore-1.bytedanceapi.com", {'Accept': 'application/json'},
                                          Credentials('', '', 'vod', 'ap-singapore-1'), 5, 5),
            'us-east-1': ServiceInfo("vod.us-east-1.bytedanceapi.com", {'Accept': 'application/json'},
                                     Credentials('', '', 'vod', 'us-east-1'), 5, 5),
        }
        service_info = service_info_map.get(region, None)
        if not service_info:
            raise Exception('Cant find the region, please check it carefully')

        return service_info

    @staticmethod
    def get_api_info():
        api_info = {
            "GetPlayInfo": ApiInfo("GET", "/", {"Action": "GetPlayInfo", "Version": "2020-08-01"}, {}, {}),
            "GetOriginalPlayInfo": ApiInfo("GET", "/", {"Action": "GetOriginalPlayInfo", "Version": "2020-08-01"}, {}, {}),
            "RedirectPlay": ApiInfo("GET", "/", {"Action": "RedirectPlay", "Version": "2020-08-01"}, {}, {}),
            "StartWorkflow": ApiInfo("POST", "/", {"Action": "StartWorkflow", "Version": "2020-08-01"}, {}, {}),
            "UploadMediaByUrl": ApiInfo("GET", "/", {"Action": "UploadMediaByUrl", "Version": "2018-01-01"}, {}, {}),
            "ApplyUpload": ApiInfo("GET", "/", {"Action": "ApplyUpload", "Version": "2018-01-01"}, {}, {}),
            "CommitUpload": ApiInfo("POST", "/", {"Action": "CommitUpload", "Version": "2018-01-01"}, {}, {}),
            "SetVideoPublishStatus": ApiInfo("POST", "/", {"Action": "SetVideoPublishStatus", "Version": "2018-01-01"}, {}, {}),
            "GetCdnDomainWeights": ApiInfo("GET", "/", {"Action": "GetCdnDomainWeights", "Version": "2019-07-01"}, {}, {}),
            "ModifyVideoInfo": ApiInfo("POST", "/", {"Action": "ModifyVideoInfo", "Version": "2018-01-01"}, {}, {}),
            "UploadVideoByUrl": ApiInfo("GET", "/", {"Action": "UploadVideoByUrl", "Version": "2020-08-01"}, {}, {}),
            "QueryUploadTaskInfo": ApiInfo("GET", "/", {"Action": "QueryUploadTaskInfo", "Version": "2020-08-01"}, {}, {}),
            # TODO 测试完毕后把Header去掉
            "ApplyUploadInfo": ApiInfo("GET", "/", {"Action": "ApplyUploadInfo", "Version": "2020-08-01"}, {}, {"X-TT-ENV": "boe_husky_feature"}),
            "CommitUploadInfo": ApiInfo("POST", "/", {"Action": "CommitUploadInfo", "Version": "2020-08-01"}, {}, {"X-TT-ENV": "boe_husky_feature"}),
        }
        return api_info

    #
    # GetPlayInfo.
    #
    # @param request VodGetPlayInfoRequest
    # @return VodGetPlayInfoResponse
    # @raise Exception
    def get_play_info(self, request: VodGetPlayInfoRequest) -> VodGetPlayInfoResponse:
        try:
            params = dict()
            jsonData = MessageToJson(request, False, True)
            params = json.loads(jsonData)
            res = self.get("GetPlayInfo", params)
            if res == '':
                raise Exception("InternalError")
            return Parse(res, VodGetPlayInfoResponse(), True)
        except Exception:
            raise

    #
    # GetOriginalPlayInfo.
    #
    # @param request VodGetOriginalPlayInfoRequest
    # @return VodGetOriginalPlayInfoResponse
    # @raise Exception
    def get_original_play_info(self, request: VodGetOriginalPlayInfoRequest) -> VodGetOriginalPlayInfoResponse:
        try:
            params = dict()
            jsonData = MessageToJson(request, False, True)
            params = json.loads(jsonData)
            res = self.get("GetOriginalPlayInfo", params)
            if res == '':
                raise Exception("InternalError")
            return Parse(res, VodGetOriginalPlayInfoResponse(), True)
        except Exception:
            raise

    def get_play_auth_token(self, params):
        token = self.get_sign_url('GetPlayInfo', params)
        ret = {'Version': 'v1', 'GetPlayInfoToken': token}
        data = json.dumps(ret)
        if sys.version_info[0] == 3:
            return base64.b64encode(data.encode('utf-8')).decode('utf-8')
        else:
            return base64.b64encode(data.decode('utf-8'))

    # upload
    def get_upload_auth_token(self, params):
        apply_token = self.get_sign_url('ApplyUpload', params)
        commit_token = self.get_sign_url('CommitUpload', params)

        ret = {'Version': 'v1', 'ApplyUploadToken': apply_token,
               'CommitUploadToken': commit_token}
        data = json.dumps(ret)
        if sys.version_info[0] == 3:
            return base64.b64encode(data.encode('utf-8')).decode('utf-8')
        else:
            return base64.b64encode(data.decode('utf-8'))

    def apply_upload(self, params):
        res = self.get('ApplyUpload', params)
        if res == '':
            raise Exception("empty response")
        res_json = json.loads(res)
        return res_json

    def apply_upload_info(self, params):
        res = self.get('ApplyUploadInfo', params)
        if res == '':
            raise Exception("empty response")
        res_json = json.loads(res)
        return res_json

    # TODO 注释，参照标准库
    def commit_upload(self, params, body):
        res = self.json('CommitUpload', params, body)
        if res == '':
            raise Exception("empty response")
        res_json = json.loads(res)
        return res_json

    def commit_upload_info(self, params, form):
        res = self.post('CommitUploadInfo', params, form)
        if res == '':
            raise Exception("empty response")
        res_json = json.loads(res)
        return res_json

    def upload_media_by_url(self, params):
        res = self.get('UploadMediaByUrl', params)
        if res == '':
            raise Exception("empty response")
        res_json = json.loads(res)
        return res_json

    def upload_video_by_url_tob(self, url_upload_request):
        return self.upload_video_by_url(url_upload_request.to_dict())

    def upload_video_by_url(self, params):
        res = self.get('UploadVideoByUrl', params)
        if res == '':
            raise Exception("empty response")
        return json.loads(res)

    def query_upload_task_info(self, url_upload_query_request):
        res = self.get('QueryUploadTaskInfo',
                       url_upload_query_request.to_dict())
        if res == '':
            raise Exception("empty response")
        return json.loads(res)

    def upload(self, space_name, file_path, file_type):
        if not os.path.isfile(file_path):
            raise Exception("no such file on file path")
        check_sum = hex(VodService.crc32(file_path))[2:]

        apply_upload_request = {'SpaceName': space_name,
                                'UploadHosts': 1, 'FileType': file_type}
        resp = self.apply_upload(apply_upload_request)
        if 'Error' in resp['ResponseMetadata']:
            raise Exception(resp['ResponseMetadata']['Error']['Message'])

        oid = resp['Result']['UploadAddress']['StoreInfos'][0]['StoreUri']
        session_key = resp['Result']['UploadAddress']['SessionKey']
        auth = resp['Result']['UploadAddress']['StoreInfos'][0]['Auth']
        host = resp['Result']['UploadAddress']['UploadHosts'][0]

        url = 'http://{}/{}'.format(host, oid)

        headers = {'Content-CRC32': check_sum, 'Authorization': auth}
        start = time.time()

        upload_status = False
        for i in range(3):
            upload_status, resp = self.put(url, file_path, headers)
            if upload_status:
                break
            else:
                print(resp)
        if not upload_status:
            raise Exception("upload error")

        cost = (time.time() - start) * 1000
        file_size = os.path.getsize(file_path)
        avg_speed = float(file_size) / float(cost)

        return oid, session_key, avg_speed

    def upload_tob(self, space_name, file_path):
        if not os.path.isfile(file_path):
            raise Exception("no such file on file path")
        check_sum = hex(VodService.crc32(file_path))[2:]

        apply_upload_info_request = {'SpaceName': space_name}
        resp = self.apply_upload_info(apply_upload_info_request)
        if 'Error' in resp['ResponseMetadata']:
            raise Exception(resp['ResponseMetadata']['Error']['Message'])

        # TODO 提出来， storeinfos 长度要判断
        oid = resp['Result']['Data']['UploadAddress']['StoreInfos'][0]['StoreUri']
        session_key = resp['Result']['Data']['UploadAddress']['SessionKey']
        auth = resp['Result']['Data']['UploadAddress']['StoreInfos'][0]['Auth']
        host = resp['Result']['Data']['UploadAddress']['UploadHosts'][0]

        url = 'http://{}/{}'.format(host, oid)

        headers = {'Content-CRC32': check_sum, 'Authorization': auth}
        start = time.time()

        upload_status = False
        for i in range(3):
            upload_status, resp = self.put(url, file_path, headers)
            if upload_status:
                break
            else:
                print(resp)
        if not upload_status:
            raise Exception("upload error")

        cost = (time.time() - start) * 1000
        file_size = os.path.getsize(file_path)
        avg_speed = float(file_size) / float(cost)

        return oid, session_key, avg_speed

    def upload_video(self, space_name, file_path, file_type, funtions_list, callback_args=''):
        oid, session_key, avg_speed = self.upload(
            space_name, file_path, file_type)

        commit_upload_request = {'SpaceName': space_name}

        body = dict()
        body['CallbackArgs'] = callback_args
        body['SessionKey'] = session_key
        body['Functions'] = funtions_list
        body = json.dumps(body)

        resp = self.commit_upload(commit_upload_request, body)
        if 'Error' in resp['ResponseMetadata']:
            raise Exception(resp['ResponseMetadata']['Error']['Message'])
        return resp['Result']

    def upload_video_tob(self, upload_video_reqeust):
        oid, session_key, avg_speed = self.upload_tob(
            upload_video_reqeust.space_name, upload_video_reqeust.file_path)

        form = dict()
        form['SessionKey'] = session_key
        form['SpaceName'] = upload_video_reqeust.space_name
        funcs_str = json.dumps(upload_video_reqeust.function_list)
        form['Functions'] = funcs_str
        form['CallbackArgs'] = upload_video_reqeust.callback_args

        resp = self.commit_upload_info({}, form)
        if 'Error' in resp['ResponseMetadata']:
            raise Exception(resp['ResponseMetadata']['Error']['Message'])
        return resp

    def upload_poster(self, vid, space_name, file_path, file_type):
        oid, session_key, avg_speed = self.upload(
            space_name, file_path, file_type)

        user_info = {'PosterUri': oid}
        body = {'SpaceName': space_name, 'Vid': vid, 'Info': user_info}
        body = json.dumps(body)

        resp = self.modify_video_info(body)
        if 'Error' in resp['ResponseMetadata']:
            raise Exception(resp['ResponseMetadata']['Error']['Message'])
        if not ('BaseResp' in resp['Result']) or not ('StatusCode' in resp['Result']['BaseResp']) or \
                resp['Result']['BaseResp']['StatusCode'] != 0:
            raise Exception("update post uri error via ModifyVideoInfo")
        return oid

    # video info
    def modify_video_info(self, body):
        res = self.json('ModifyVideoInfo', {}, body)
        if res == '':
            raise Exception("empty response")
        res_json = json.loads(res)
        return res_json

    @staticmethod
    def crc32(file_path):
        prev = 0
        for eachLine in open(file_path, "rb"):
            prev = crc32(eachLine, prev)
        return prev & 0xFFFFFFFF

    #
        # StartWorkflow.
        #
    # @param request VodStartWorkflowRequest
    # @return VodStartWorkflowResponse
    # @raise Exception
    def start_workflow(self, request: VodStartWorkflowRequest) -> VodStartWorkflowResponse:
        try:
            params = dict()
            jsonData = MessageToJson(request, False, True)
            params = json.loads(jsonData)
            res = self.get("StartWorkflow", params)
            if res == '':
                raise Exception("InternalError")
            return Parse(res, VodStartWorkflowResponse(), True)
        except Exception:
            raise

    # publish
    def set_video_publish_status(self, body):
        params = {}
        res = self.json('SetVideoPublishStatus', params, json.dumps(body))
        if res == '':
            raise Exception("empty response")
        res_json = json.loads(res)
        return res_json

    # img
    def get_domain_weights(self, space_name):
        params = {'SpaceName': space_name}
        res = self.get('GetCdnDomainWeights', params)
        if res == '':
            raise Exception("empty response")
        res_json = json.loads(res)
        if not ('Error' in res_json['ResponseMetadata']) and (space_name in res_json['Result']):
            return res_json['Result'][space_name]
        else:
            return {}

    def set_fallback_domain_weights(self, fallback_domain_weights):
        if type(fallback_domain_weights) == dict and fallback_domain_weights:
            self.fallback_domain_weights = fallback_domain_weights
            return True
        else:
            return False

    def async_update_domain_weights(self, space_name):
        while True:
            time.sleep(self.update_interval)

            domain_weights = self.get_domain_weights(space_name)
            self.lock.acquire()
            if domain_weights:
                self.domain_cache[space_name] = domain_weights
            else:
                self.domain_cache[space_name] = self.fallback_domain_weights
            self.lock.release()

    def get_domain_info(self, space_name):
        self.lock.acquire()
        if not (space_name in self.domain_cache):
            domain_weights = self.get_domain_weights(space_name)
            if domain_weights:
                self.domain_cache[space_name] = domain_weights
            else:
                self.domain_cache[space_name] = self.fallback_domain_weights

            t = threading.Thread(
                target=self.async_update_domain_weights, args=(space_name,))
            t.setDaemon(True)
            t.start()
        self.lock.release()
        cache = self.domain_cache[space_name]

        main_domain = VodService.rand_weights(cache, '')
        backup_domain = VodService.rand_weights(cache, main_domain)
        return {'MainDomain': main_domain, 'BackupDomain': backup_domain}

    def get_poster_url(self, space_name, uri, option):
        domain_info = self.get_domain_info(space_name)
        proto = HTTP
        if option.isHttps:
            proto = HTTPS
        format = FORMAT_ORIGINAL
        if option.format:
            format = option.format
        tpl = VOD_TPL_NOOP
        if option.tpl:
            tpl = option.tpl
        if not (tpl == VOD_TPL_OBJ or tpl == VOD_TPL_NOOP):
            tpl = '{}:{}:{}'.format(option.tpl, option.width, option.height)

        main_url = '{}://{}/{}~{}.{}'.format(proto,
                                             domain_info['MainDomain'], uri, tpl, format)
        backup_url = '{}://{}/{}~{}.{}'.format(proto,
                                               domain_info['BackupDomain'], uri, tpl, format)
        return {'MainUrl': main_url, 'BackupUrl': backup_url}

    @staticmethod
    def rand_weights(domain_map, exclude_domain):
        weight_sum = 0
        for key in domain_map:
            if key == exclude_domain:
                continue
            weight_sum += domain_map[key]
        if weight_sum <= 0:
            return ''

        r = random.randint(1, weight_sum)
        for key in domain_map:
            if key == exclude_domain:
                continue
            r -= domain_map[key]
            if r <= 0:
                return key
        return ''

    def get_video_play_auth_with_expired_time(self, vid_list, stream_type_list, watermark_list, expired_time):
        actions = [ACTION_VOD_GET_PLAY_INFO]
        resources = []

        self.add_resource_format(vid_list, resources, RESOURCE_VIDEO_FORMAT)
        self.add_resource_format(
            stream_type_list, resources, RESOURCE_STREAM_TYPE_FORMAT)
        self.add_resource_format(
            watermark_list, resources, RESOURCE_WATERMARK_FORMAT)

        statement = Statement.new_allow_statement(actions, resources)
        inline_policy = Policy([statement])
        return self.sign_sts2(inline_policy, expired_time)

    @staticmethod
    def add_resource_format(v_list, resources, resource_format):
        if len(v_list) == 0:
            resources.append(resource_format % STAR)
        else:
            for value in v_list:
                resources.append(resource_format % value)

    def get_video_play_auth(self, vid_list, stream_type_list, watermark_list):
        return self.get_video_play_auth_with_expired_time(vid_list, stream_type_list, watermark_list, 60 * 60)
