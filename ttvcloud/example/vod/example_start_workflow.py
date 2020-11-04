# coding:utf-8
from __future__ import print_function

from ttvcloud.models.vod.request.request_vod_pb2 import *
from ttvcloud.vod.VodService import VodService

if __name__ == '__main__':
    vod_service = VodService()
    # call below method if you dont set ak and sk in $HOME/.vcloud/config
    # vod_service.set_ak('ak')
    # vod_service.set_sk('sk')
    try:
        req = VodStartWorkflowRequest()
        req.Vid = 'xxxx'
        req.TemplateId = 'xxx'
        resp = vod_service.start_workflow(req)
    except Exception:
        raise
