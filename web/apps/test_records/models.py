from datetime import datetime
from django.utils import timezone
from django.db import models

# Create your models here.
from users.models import UserMachine


class TestBranch(models.Model):
    """
    test brand
    """
    branch_name = models.CharField(max_length=128, unique=True,verbose_name="branch name", help_text="branch name")
    branch_order = models.IntegerField(default=5,verbose_name=" branch order", help_text="order in all the  branch")
    is_show = models.BooleanField(verbose_name="branch isshow", default=True, help_text="branch isshow")
    is_accept = models.BooleanField(verbose_name="branch weather accept accept new reports", default=True, help_text="branch weather accept new reports")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="branch added time",
                                    help_text="branch added time")

    class Meta:
        verbose_name = "test branch"
        verbose_name_plural = "test branch"

    def __str__(self):
        return self.branch_name


class TestCategory(models.Model):
    """
    tests category
    """
    cate_name = models.CharField(max_length=64, verbose_name="cate name", help_text="cate name")
    cate_sn = models.CharField(max_length=32, unique=True, verbose_name="cate sn", help_text="cate sn")
    # cate_parent = models.ForeignKey("self", verbose_name="parent category", related_name="sub_cat", help_text="parent category")
    cate_order = models.IntegerField(verbose_name="cate order", help_text="order in the current level")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="add time", help_text="category added time")

    class Meta:
        verbose_name = "tests category"
        verbose_name_plural = "tests category"

    def __str__(self):
        return self.cate_name


class PGInfo(models.Model):
    """
    pg info

    "settings": {
        "checkpoint_timeout": "15min",
        "log_temp_files": "32",
        "work_mem": "64MB",
        "log_line_prefix": "%n %t ",
        "shared_buffers": "1GB",
        "log_autovacuum_min_duration": "0",
        "checkpoint_completion_target": "0.9",
        "maintenance_work_mem": "128MB",
        "log_checkpoints": "on",
        "max_wal_size": "4GB",
        "min_wal_size": "2GB"
    }
    """
    checkpoint_timeout =models.IntegerField(verbose_name="checkpoint_timeout", help_text="checkpoint_timeout")
    log_temp_files = models.IntegerField(verbose_name="log_temp_files", help_text="log_temp_files")
    work_mem = models.IntegerField(verbose_name="work_mem", help_text="work_mem")
    log_line_prefix = models.CharField(max_length=64,verbose_name="checkpoint_timeout", help_text="checkpoint_timeout")
    shared_buffers = models.IntegerField(verbose_name="shared_buffers", help_text="shared_buffers")
    log_autovacuum_min_duration =models.IntegerField(verbose_name="log_autovacuum_min_duration", help_text="log_autovacuum_min_duration")


    checkpoint_completion_target =models.DecimalField(max_digits=8, decimal_places=4,verbose_name="checkpoint_completion_target", help_text="checkpoint_completion_target")
    maintenance_work_mem = models.IntegerField(verbose_name="maintenance_work_mem", help_text="maintenance_work_mem")

    SWITCH_CHOICE = (
        (1, 'on'),
        (2, 'off')
    )
    log_checkpoints = models.IntegerField(choices=SWITCH_CHOICE,verbose_name="log_checkpoints", help_text="log_checkpoints")
    max_wal_size =models.IntegerField(verbose_name="max_wal_size", help_text="max_wal_size")
    min_wal_size =models.IntegerField(verbose_name="min_wal_size", help_text="min_wal_size")

    # pg_branch = models.ForeignKey(TestBranch, verbose_name="pg branch", help_text="pg branch")

    class Meta:
        verbose_name = "pg info"
        verbose_name_plural = "pg info"


class MetaInfo(models.Model):
    """
    meta info
    """
    date = models.DateTimeField(verbose_name="date", help_text="date")
    uname = models.TextField(verbose_name="uname", help_text="uname")
    benchmark = models.TextField(verbose_name="benchmark", help_text="benchmark")
    name = models.TextField(verbose_name="name", help_text="name")

    class Meta:
        verbose_name = "meta info"
        verbose_name_plural = "meta info"


class LinuxInfo(models.Model):
    """
    linux info
    """
    mounts = models.TextField(verbose_name="mounts", help_text="mounts")
    cpuinfo = models.TextField(verbose_name="cpuinfo", help_text="cpuinfo")
    sysctl = models.TextField(verbose_name="sysctl", help_text="sysctl")
    meminfo = models.TextField(verbose_name="meminfo", help_text="meminfo")

    class Meta:
        verbose_name = "linux info"
        verbose_name_plural = "linux info"

    def __str__(self):
        return self.mounts


class TestRecord(models.Model):
    """
    test record
    """
    branch = models.ForeignKey(TestBranch, verbose_name="pg branch", help_text="pg branch")
    test_machine = models.ForeignKey(UserMachine, verbose_name="test owner",
                                     help_text="person who add this test item")
    pg_info = models.ForeignKey(PGInfo, verbose_name="pg info", help_text="pg info")
    meta_info = models.ForeignKey(MetaInfo, verbose_name="meta info", help_text="meta info")
    linux_info = models.ForeignKey(LinuxInfo, verbose_name="linux info", help_text="linux info")
    test_desc = models.TextField(verbose_name="test desc", help_text="test desc")
    # test_branch_id = models.ForeignKey(TestBranch, verbose_name="test category", help_text="test category")
    meta_time = models.DateTimeField(default=timezone.now, verbose_name="meta time")
    hash = models.CharField(unique=True, default='', max_length=128, verbose_name="record hash",
                            help_text="record hash")
    uuid = models.CharField(unique=True, default='', max_length=64, verbose_name="record uuid", help_text="record uuid")
    commit = models.CharField(max_length=64, verbose_name="record commit", help_text="record commit")

    add_time = models.DateTimeField(default=timezone.now, verbose_name="test added time")

    class Meta:
        verbose_name = "tests"
        verbose_name_plural = "tests"


# class AbstractTestDataSet(models.Model):
#     prev = models.ForeignKey('self',blank=True, null=True, related_name='none')
#     class Meta:
#         abstract = True

class TestDataSet(models.Model):
    test_record = models.ForeignKey(TestRecord, verbose_name="test record id", help_text="test record id")
    test_cate = models.ForeignKey(TestCategory, verbose_name="test cate id", help_text="test cate id")
    clients = models.IntegerField(verbose_name="clients", help_text="clients of the test dataset")
    scale = models.IntegerField(verbose_name="scale", help_text="scale of the test dataset")
    std = models.DecimalField(max_digits=18, decimal_places=8, verbose_name="std", help_text="std of the test dataset")
    metric = models.DecimalField(max_digits=18, decimal_places=8, verbose_name="metric",
                                 help_text="metric of the test dataset")
    median = models.DecimalField(max_digits=18, decimal_places=8, verbose_name="median",
                                 help_text="median of the test dataset")

    STATUS_CHOICE = (
        (-1, 'none'),
        (1, 'improved'),
        (2, 'quo'),
        (3, 'regressive'),
    )
    status = models.IntegerField(choices=STATUS_CHOICE, verbose_name="status", help_text="status of this dataset")
    percentage = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="percentage",
                                     help_text="percentage compared to previous dataset")

    prev = models.ForeignKey('self', blank=True, null=True, related_name='prev1',
                             verbose_name="previous test dataset id", help_text="previous test dataset id")
    # prev = models.ForeignKey('self',verbose_name="previous test dataset id", help_text="previous test dataset id")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="test dataset time")

    class Meta:
        verbose_name = "test dataset"
        verbose_name_plural = "test dataset"


from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=TestDataSet)
def calc_status(sender, instance, **kwargs):
    print('dataset:' + str(instance.id) + "  prev:" + str(instance.prev) + " will be save ")

    # record_id = instance.test_record.id
    machine_id = instance.test_record.test_machine_id
    add_time = instance.test_record.add_time
    branch = instance.test_record.branch
    prevRecord = TestRecord.objects.order_by('-add_time').filter(test_machine_id=machine_id,branch=branch,
                                                                 add_time__lt=add_time).first()
    if (prevRecord == None):
        print("prev record not found")
        return
    # print("previd is: " + str(prevRecord.id))
    prevTestDataSet = TestDataSet.objects.filter(test_record_id=prevRecord.id, scale=instance.scale,
                                                 clients=instance.clients, test_cate_id=instance.test_cate_id).first()

    if (prevTestDataSet == None):
        # print("prev dataset not found")
        return

    # print("prev dataset is: " + str(prevTestDataSet.id))

    percentage = (instance.metric - prevTestDataSet.metric) / prevTestDataSet.metric
    # print('instance.metric is:' + str(instance.metric))
    # print('prevTestDataSet.metric is:' + str(prevTestDataSet.metric))
    # print('percentage is:' + str(percentage))
    status = 0
    if (percentage >= 0.05):
        status = 1
    elif (percentage <= -0.05):
        status = 3
    else:
        status = 2

    instance.percentage = percentage
    instance.status = status
    instance.prev_id = prevTestDataSet.id

    return


class TestResult(models.Model):
    """
    test result sample:

    "latency": -1,
    "scale": "10",
    "end": 1526184453.133798,
    "clients": "2",
    "start": 1526184333.102856,
    "run": 0,
    "threads": "2",
    "mode": "simple",
    "duration": "120",
    "tps": "369.666116",
    "read-only": false

    """

    test_dataset = models.ForeignKey(TestDataSet, verbose_name="test dataset id", help_text="test dataset id")
    # test_cate = models.ForeignKey(TestCategory, verbose_name="test category", help_text="test category")
    latency = models.IntegerField(verbose_name="latency", help_text="latency of the test result")
    scale = models.IntegerField(verbose_name="scale", help_text="scale of the test result")
    end = models.DecimalField(max_digits=16, decimal_places=6, verbose_name="end",
                              help_text="endtime of the test result")
    clients = models.IntegerField(verbose_name="clients", help_text="clients of the test result")
    start = models.DecimalField(max_digits=16, decimal_places=6, verbose_name="start",
                                help_text="starttime of the test result")
    tps = models.DecimalField(default=0, max_digits=18, decimal_places=6, verbose_name="tps",
                              help_text="tps of the test result")
    run = models.IntegerField(verbose_name="run", help_text="run number")
    threads = models.IntegerField(verbose_name="threads", help_text="threads of the test result")

    MODE_CHOICE = (
        (1, 'simple'),
        (2, 'other'),
    )
    mode = models.IntegerField(choices=MODE_CHOICE, verbose_name="mode", help_text="test mode")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="test result added time")

    class Meta:
        verbose_name = "test result"
        verbose_name_plural = "test result"
