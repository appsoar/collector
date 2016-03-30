# -*- coding: utf-8 -*-
# Copyright (c) 20016-2016 The Cloudsoar.
# See LICENSE for details.


MAIN_DB_NAME   = "cloudsoar"
ID             = "_id"

IDENTITY_TABLE         = "identity"

USER_TABLE             = "User"
USER_GROUP_TABLE       = "Group"
REPOSITORY_TABLE       = "Repository"
NAMESPACE_TABLE        = "Namespace" 
COMMENT_TABLE          = "Comment"
TAG_TABLE              = "Tags"
IMAGE_TABLE            = "Image"
LAYER_TABLE            = "Layer"
USER_GROUP_TABLE       = "User_Group"
GROUP_NAMESPACE_TABLE  = "Group_Namespace"


NOTIFICATION_TABLE     = "Notification"




SCHEDULE_TABLE         = "Schedule"     # 调度任务信息
SCHEDULE_JOB_TABLE     = "Jobs"         # Scheduler 库使用的私有的数据表

TASK_TABLE             = "Task"
SUB_TASK_TABLE         = "SubTask"      # 存放子任务，子任务是任务计划的一部分， 不能单独恢复 
SYNCTASK               = "SyncTask"
CONFIG_TABLE           = "Configure"







