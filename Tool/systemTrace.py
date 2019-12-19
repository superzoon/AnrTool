
from os.path import isfile,sep
from Tool import toolUtils
import re

UN_REGISTER_MAP = list()

class TraceLine:
    PATTERN_LINE = r'^[\s]*(.+)-([\d]+)[\s]+\(([\d|-|\s]+)\)[\s]+\[([\d]+)\][\s]+([d|X|\.])([N|n|p|\.])([H|h|s|\.])([0-9|a-f|\.])[\s]+([\d]+\.[\d]+):\s+([\S]+):\s(.*)$'
    PATTERN_LINE = '^[\s]*(.+)-([\d]+)[\s]+\(([^\)]+)\)[\s]+\[([\d]+)\][\s]+([d|X|\.])([N|n|p|\.])([H|h|s|\.])([0-9|a-f|\.])[\s]+([\d]+\.[\d]+):\s+([\S]+):\s(.*)$'
    '''
    <!-- BEGIN TRACE -->
      <script class="trace-data" type="application/text">
    # tracer: nop
    #
    # entries-in-buffer/entries-written: 201593/201593   #P:8
    #
    #                                      _-----=> irqs-off
    #                                     / _----=> need-resched
    #                                    | / _---=> hardirq/softirq
    #                                    || / _--=> preempt-depth
    #                                    ||| /     delay
    #           TASK-PID    TGID   CPU#  ||||    TIMESTAMP  FUNCTION
    #              | |        |      |   ||||       |         |
              <idle>-0     (-----) [002] dn.1  1507.655129: cpu_pred_hist: idx:0 resi:13 sample:4 tmr:0
               <...>-976   (  922) [003] d..4  1507.655130: sched_wakeup: comm=ndroid.systemui pid=2217 prio=110 target_cpu=002
         OomAdjuster-1466  ( 1070) [006] ....  1509.655935: cgroup_attach_task: dst_root=2 dst_id=2 dst_level=1 dst_path=/background pid=5747 comm=Thread-20
      </script>
    <!-- END TRACE -->
    '''
    def __init__(self, task:str, pid:int, tgid:int, cpuId:int, irqsOff:str, needResched:str, irq:str, preemptDepth:str, timestamp:float, eventName, details, systemTrace):
        '''
        :param task: name or ... or idle 名称
        :param pid: 进程id
        :param tgid: 线程id
        :param cpuId: 使用的cpu号
        :param irqsOff: 终端请求了 [dX.]
        :param needResched: 需要resched [Nnp.]
        :param irq: 中断[Hhs.]
        :param preemptDepth: 优先等级[0-9a-f.]
        :param timestamp: 时间戳
        '''
        self.task:str = task
        self.pid: int = pid
        self.tgid: int = tgid
        self.cpuId: int = cpuId
        self.irqsOff: chr = irqsOff
        self.needResched: chr = needResched
        self.irq: chr = irq
        self.preemptDepth: chr = preemptDepth
        self.timestamp: float = timestamp
        self.eventName = eventName
        self.systemTrace = systemTrace
        self.parseEvent(eventName, details)

    def parseEvent(self, eventName:str, details:str):
        self.test = False
        if eventName and eventName.startswith('sched_'):
            self.parseSchedEvent(eventName, details)
        elif eventName and eventName.startswith('binder_'):
            self.parseBinderEvent(eventName, details)
        elif eventName and eventName.startswith('kProcess'):
            self.parseKProcessEvent(eventName, details)
        elif eventName and eventName.startswith('kThread'):
            self.parseKThreadEvent(eventName, details)
        elif eventName and eventName.startswith('cpufreq_'):
            self.parseCpufreqEvent(eventName, details)
        elif eventName and eventName.startswith('f2fs_'):
            self.parseF2fsEvent(eventName, details)
        elif eventName and eventName.startswith('ext4_'):
            self.parseExt4Event(eventName, details)
        elif eventName and eventName.startswith('i2c_'):
            self.parseI2cEvent(eventName, details)
        elif eventName and eventName.startswith('i915_'):
            self.parseI915Event(eventName, details)
        elif eventName and eventName.startswith('exynos_'):
            self.parseExynosEvent(eventName, details)
        elif eventName and eventName.startswith('clock_'):
            self.parseClockEvent(eventName, details)
        elif eventName and eventName.startswith('clk_'):
            self.parseClkEvent(eventName, details)
        elif eventName and eventName.startswith('fence_'):
            self.parseFenceEvent(eventName, details)
        elif eventName and eventName.startswith('regulator_'):
            self.parseRegulatorEvent(eventName, details)
        elif eventName and eventName.startswith('tracing_'):
            self.parseTracingEvent(eventName, details)
        elif eventName and eventName.startswith('hrtimer_'):
            self.parseHrtimerEvent(eventName, details)
        elif eventName and eventName.startswith('timer_'):
            self.parseTimerEvent(eventName, details)
        elif eventName and eventName.startswith('mm_'):
            self.parseMmEvent(eventName, details)
        elif eventName and eventName.startswith('workqueue_'):
            self.parseWorkqueueEvent(eventName, details)
        elif eventName and eventName.startswith('irq_'):
            self.parseIrqEvent(eventName, details)
        elif eventName and eventName.startswith('softirq_'):
            self.parseSoftirqEvent(eventName, details)
        elif eventName and eventName.startswith('cpu_'):
            self.parseCpuEvent(eventName, details)
        elif eventName and eventName.startswith('mali_'):
            self.parseMaliEvent(eventName, details)
        elif eventName and eventName.startswith('dma_'):
           self.parseDmaEvent(eventName, details)
        elif eventName and eventName.startswith('sde_'):
            self.parseSdeEvent(eventName, details)
        elif eventName and eventName.startswith('cgroup_'):
            self.parseCgroupEvent(eventName, details)
        elif eventName and eventName.startswith('task_'):
            self.parseTaskEvent(eventName, details)
        elif eventName and eventName.startswith('block_'):
            self.parseBlockEvent(eventName, details)
        elif eventName and eventName.startswith('power_'):
            self.parsePowerEvent(eventName, details)
        elif eventName and eventName.startswith('sync_'):
            self.parseSyncEvent(eventName, details)
        elif eventName and eventName.startswith('0'):
            self.parseZeroEvent(eventName, details)
        elif eventName and eventName.startswith('graph_'):
            self.parseGraphEvent(eventName, details)
        elif eventName and eventName.startswith('preempt_'):
            self.parsePreemptEvent(eventName, details)
        elif eventName and eventName.startswith('ipi_'):
            self.parseIpiEvent(eventName, details)
        else:
            self.parseDefaultEvent(eventName, details)

    def parseCpufreqEvent(self, eventName: str, details: str):
        if 'cpufreq_interactive_up' == eventName:
            eventName = 'CpufreqParser.prototype.cpufreqUpDownEvent.bind(this)'
        elif 'cpufreq_interactive_down' == eventName:
            eventName = 'CpufreqParser.prototype.cpufreqUpDownEvent.bind(this)'
        elif 'cpufreq_interactive_already' == eventName:
            eventName = 'CpufreqParser.prototype.cpufreqTargetEvent.bind(this)'
        elif 'cpufreq_interactive_notyet' == eventName:
            eventName = 'CpufreqParser.prototype.cpufreqTargetEvent.bind(this)'
        elif 'cpufreq_interactive_setspeed' == eventName:
            eventName = 'CpufreqParser.prototype.cpufreqTargetEvent.bind(this)'
        elif 'cpufreq_interactive_target' == eventName:
            eventName = 'CpufreqParser.prototype.cpufreqTargetEvent.bind(this)'
        elif 'cpufreq_interactive_boost' == eventName:
            eventName = 'CpufreqParser.prototype.cpufreqBoostUnboostEvent.bind(this)'
        elif 'cpufreq_interactive_unboost' == eventName:
            eventName = 'CpufreqParser.prototype.cpufreqBoostUnboostEvent.bind(this)'

    def parseKThreadEvent(self, eventName: str, details: str):
        if 'kThreadStartOpcode' == eventName:
            eventName = 'ThreadParser.prototype.decodeStart.bind(this)'
        elif 'kThreadEndOpcode' == eventName:
            eventName = 'ThreadParser.prototype.decodeEnd.bind(this)'
        elif 'kThreadDCStartOpcode' == eventName:
            eventName = 'ThreadParser.prototype.decodeDCStart.bind(this)'
        elif 'kThreadDCEndOpcode' == eventName:
            eventName = 'ThreadParser.prototype.decodeDCEnd.bind(this)'
        elif 'kThreadCSwitchOpcode' == eventName:
            eventName = 'ThreadParser.prototype.decodeCSwitch.bind(this)'

    def parseKProcessEvent(self, eventName: str, details: str):
        if 'kProcessStartOpcode' == eventName:
            eventName = 'ProcessParser.prototype.decodeStart.bind(this)'
        elif 'kProcessEndOpcode' == eventName:
            eventName = 'ProcessParser.prototype.decodeEnd.bind(this)'
        elif 'kProcessDCStartOpcode' == eventName:
            eventName = 'ProcessParser.prototype.decodeDCStart.bind(this)'
        elif 'kProcessDCEndOpcode' == eventName:
            eventName = 'ProcessParser.prototype.decodeDCEnd.bind(this)'
        elif 'kProcessDefunctOpcode' == eventName:
            eventName = 'ProcessParser.prototype.decodeDefunct.bind(this)'

    def parseBinderEvent(self, eventName: str, details: str):
        if 'binder_locked' == eventName:
            eventName = 'BinderParser.prototype.binderLocked.bind(this)'
        elif 'binder_unlock' == eventName:
            eventName = 'BinderParser.prototype.binderUnlock.bind(this)'
        elif 'binder_lock' == eventName:
            eventName = 'BinderParser.prototype.binderLock.bind(this)'
        elif 'binder_transaction' == eventName:
            eventName = 'BinderParser.prototype.binderTransaction.bind(this)'
        elif 'binder_transaction_received' == eventName:
            eventName = 'BinderParser.prototype.binderTransactionReceived.bind(this)'
        elif 'binder_transaction_alloc_buf' == eventName:
            eventName = 'BinderParser.prototype.binderTransactionAllocBuf.bind(this)'

    # 'prev_comm=ndroid.systemui prev_pid=15559 prev_prio=110 prev_state=S ==> next_comm=Binder:916_3 next_pid=1111 next_prio=120'
    PATTERN_SCHED_SWITCH = 'prev_comm=(.+) prev_pid=(\d+) prev_prio=(\d+) ' + 'prev_state=(\S\\+?|\S\|\S) ==> ' + 'next_comm=(.+) next_pid=(\d+) next_prio=(\d+)'
    # 'comm=ipacm-diag pid=641 prio=120 target_cpu=000'
    # 'comm=HwBinder:781_2 pid=1742 prio=120 target_cpu=006'
    PATTERN_SCHED_WAKEUP_WAKEING = 'comm=(.+) pid=(\d+) prio=(\d+)(?: success=\d+)? target_cpu=(\d+)'
    def parseSchedEvent(self, eventName:str, details:str):
        if 'sched_switch' == eventName:
            match = re.match(TraceLine.PATTERN_SCHED_SWITCH, details)
            if match:
                self._prev_comm_ = match.group(1)
                self._prev_pid_ = int(match.group(2))
                self._prev_prio_ = int(match.group(3))
                self._prev_state_ = match.group(4)#S stop, I , R+ running,R runnable,X , Z
                self._next_comm_ = match.group(5)
                self._next_pid_ = int(match.group(6))
                self._next_prio_ = int(match.group(7))
                self.systemTrace.schedSwitchs.append(self)
            if str(29162) in details:
                self.test = True

        elif 'sched_wakeup' == eventName or 'sched_waking' == eventName:
            match = re.match(TraceLine.PATTERN_SCHED_WAKEUP_WAKEING, details)
            if match:
                self._comm_ = match.group(1)
                self._fromPid_ = self.pid
                self._pid_ = int(match.group(2))
                self._prio_ = int(match.group(3))
                if len(match.groups()) == 5:
                    self._target_cpu_ = match.group(5)
                else:
                    self._target_cpu_ = match.group(4)
                if 'sched_wakeup' == eventName:
                    self.systemTrace.schedWakeups.append(self)
                else:
                    self.systemTrace.schedWakings.append(self)
            if str(29162) in details:
                self.test = True

        elif 'sched_blocked_reason' == eventName:
            eventName = 'SchedParser.prototype.schedBlockedEvent.bind(this)'
        elif 'sched_isolate' == eventName:
            eventName = 'xx'
        elif 'sched_migrate_task' == eventName:
            eventName = 'xx'
        elif 'sched_pi_setprio' == eventName:
            eventName = 'xx'
        elif 'sched_process_exit' == eventName:
            eventName = 'xx'
        elif 'sched_wakeup_new' == eventName:
            eventName = 'xx'
        elif 'sched_cpu_hotplug' == eventName:
            tag = 'SchedParser.prototype.schedCpuHotplugEvent.bind(this)'

    def parseF2fsEvent(self, eventName:str, details:str):
        if 'f2fs_write_begin' == eventName:
            eventName = 'DiskParser.prototype.f2fsWriteBeginEvent.bind(this)'
        elif 'f2fs_write_end' == eventName:
            eventName = 'DiskParser.prototype.f2fsWriteEndEvent.bind(this)'
        elif 'f2fs_sync_file_enter' == eventName:
            eventName = 'DiskParser.prototype.f2fsSyncFileEnterEvent.bind(this)'
        elif 'f2fs_sync_file_exit' == eventName:
            eventName = 'DiskParser.prototype.f2fsSyncFileExitEvent.bind(this)'

    def parseExt4Event(self, eventName:str, details:str):
        if 'ext4_sync_file_enter' == eventName:
            eventName = 'DiskParser.prototype.ext4SyncFileEnterEvent.bind(this)'
        elif 'ext4_sync_file_exit' == eventName:
            eventName = 'DiskParser.prototype.ext4SyncFileExitEvent.bind(this)'
        elif 'ext4_da_write_begin' == eventName:
            eventName = 'DiskParser.prototype.ext4WriteBeginEvent.bind(this)'
        elif 'ext4_da_write_end' == eventName:
            eventName = 'DiskParser.prototype.ext4WriteEndEvent.bind(this)'

    def parseI2cEvent(self, eventName: str, details: str):
        if 'i2c_write:HandleTimer' == eventName:
            eventName = 'I2cParser.prototype.i2cWriteEvent.bind(this)'
        elif 'i2c_read' == eventName:
            eventName = 'I2cParser.prototype.i2cReadEvent.bind(this)'
        elif 'i2c_write' == eventName:
            eventName = 'xx'
        elif 'i2c_reply' == eventName:
            eventName = 'I2cParser.prototype.i2cReplyEvent.bind(this)'
        elif 'i2c_result' == eventName:
            eventName = 'I2cParser.prototype.i2cResultEvent.bind(this)'

    def parseI915Event(self, eventName: str, details: str):
        if 'i915_gem_object_create' == eventName:
            eventName = 'I915Parser.prototype.gemObjectCreateEvent.bind(this)'
        elif 'i915_gem_object_bind' == eventName:
            eventName = 'I915Parser.prototype.gemObjectBindEvent.bind(this)'
        elif 'i915_gem_object_unbind' == eventName:
            eventName = 'I915Parser.prototype.gemObjectBindEvent.bind(this)'
        elif 'i915_gem_object_change_domain' == eventName:
            eventName = 'I915Parser.prototype.gemObjectChangeDomainEvent.bind(this)'
        elif 'i915_gem_object_pread' == eventName:
            eventName = 'I915Parser.prototype.gemObjectPreadWriteEvent.bind(this)'
        elif 'i915_gem_object_pwrite' == eventName:
            eventName = 'I915Parser.prototype.gemObjectPreadWriteEvent.bind(this)'
        elif 'i915_gem_object_fault' == eventName:
            eventName = 'I915Parser.prototype.gemObjectFaultEvent.bind(this)'
        elif 'i915_gem_object_clflush' == eventName:
            eventName = 'I915Parser.prototype.gemObjectDestroyEvent.bind(this)'
        elif 'i915_gem_object_destroy' == eventName:
            eventName = 'I915Parser.prototype.gemObjectDestroyEvent.bind(this)'
        elif 'i915_gem_ring_dispatch' == eventName:
            eventName = 'I915Parser.prototype.gemRingDispatchEvent.bind(this)'
        elif 'i915_gem_ring_flush' == eventName:
            eventName = 'I915Parser.prototype.gemRingFlushEvent.bind(this)'
        elif 'i915_gem_request' == eventName:
            eventName = 'I915Parser.prototype.gemRequestEvent.bind(this)'
        elif 'i915_gem_request_add' == eventName:
            eventName = 'I915Parser.prototype.gemRequestEvent.bind(this)'
        elif 'i915_gem_request_complete' == eventName:
            eventName = 'I915Parser.prototype.gemRequestEvent.bind(this)'
        elif 'i915_gem_request_retire' == eventName:
            eventName = 'I915Parser.prototype.gemRequestEvent.bind(this)'
        elif 'i915_gem_request_wait_begin' == eventName:
            eventName = 'I915Parser.prototype.gemRequestEvent.bind(this)'
        elif 'i915_gem_request_wait_end' == eventName:
            eventName = 'I915Parser.prototype.gemRequestEvent.bind(this)'
        elif 'i915_gem_ring_wait_begin' == eventName:
            eventName = 'I915Parser.prototype.gemRingWaitEvent.bind(this)'
        elif 'i915_gem_ring_wait_end' == eventName:
            eventName = 'I915Parser.prototype.gemRingWaitEvent.bind(this)'
        elif 'i915_reg_rw' == eventName:
            eventName = 'I915Parser.prototype.regRWEvent.bind(this)'
        elif 'i915_flip_request' == eventName:
            eventName = 'I915Parser.prototype.flipEvent.bind(this)'
        elif 'i915_flip_complete' == eventName:
            eventName = 'I915Parser.prototype.flipEvent.bind(this)'

    def parseExynosEvent(self, eventName: str, details: str):
        if 'exynos_busfreq_target_int' == eventName:
            eventName = 'ExynosParser.prototype.busfreqTargetIntEvent.bind(this)'
        elif 'exynos_busfreq_target_mif' == eventName:
            eventName = 'ExynosParser.prototype.busfreqTargetMifEvent.bind(this)'
        elif 'exynos_page_flip_state' == eventName:
            eventName = 'ExynosParser.prototype.pageFlipStateEvent.bind(this)'

    def parseClockEvent(self, eventName: str, details: str):
        if 'clock_set_rate' == eventName:
            eventName = ',ClockParser.prototype.traceMarkWriteClockEvent.bind(this)'
        elif 'clock_enable' == eventName:
            eventName = 'ClockParser.prototype.traceMarkWriteClockOnOffEvent.bind(this)'
        elif 'clock_disable' == eventName:
            eventName = 'ClockParser.prototype.traceMarkWriteClockOnOffEvent.bind(this)'

    def parseClkEvent(self, eventName: str, details: str):
        if 'clk_set_rate' == eventName:
            eventName = 'ClockParser.prototype.traceMarkWriteClkEvent.bind(this)'
        elif 'clk_enable' == eventName:
            eventName = 'ClockParser.prototype.traceMarkWriteClkOnEvent.bind(this)'
        elif 'clk_disable' == eventName:
            eventName = 'ClockParser.prototype.traceMarkWriteClkOffEvent.bind(this)'

    def parseFenceEvent(self, eventName: str, details: str):
        if 'fence_init' == eventName:
            eventName = 'FenceParser.prototype.initEvent.bind(this)'
        elif 'fence_destroy' == eventName:
            eventName = 'FenceParser.prototype.fenceDestroyEvent.bind(this)'
        elif 'fence_enable_signal' == eventName:
            eventName = 'FenceParser.prototype.fenceEnableSignalEvent.bind(this)'
        elif 'fence_signaled' == eventName:
            eventName = 'FenceParser.prototype.fenceSignaledEvent.bind(this)'

    def parseRegulatorEvent(self, eventName: str, details: str):
        if 'regulator_enable' == eventName:
            eventName = 'RegulatorParser.prototype.regulatorEnableEvent.bind(this)'
        elif 'regulator_enable_delay' == eventName:
            eventName = 'RegulatorParser.prototype.regulatorEnableDelayEvent.bind(this)'
        elif 'regulator_enable_complete' == eventName:
            eventName = 'RegulatorParser.prototype.regulatorEnableCompleteEvent.bind(this)'
        elif 'regulator_disable' == eventName:
            eventName = 'RegulatorParser.prototype.regulatorDisableEvent.bind(this)'
        elif 'regulator_disable_complete' == eventName:
            eventName = 'RegulatorParser.prototype.regulatorDisableCompleteEvent.bind(this)'
        elif 'regulator_set_voltage' == eventName:
            eventName = 'RegulatorParser.prototype.regulatorSetVoltageEvent.bind(this)'
        elif 'regulator_set_voltage_complete' == eventName:
            eventName = 'RegulatorParser.prototype.regulatorSetVoltageCompleteEvent.bind(this)'

    def parseTracingEvent(self, eventName: str, details: str):
        if 'tracing_mark_write:mali_driver' == eventName:
            eventName = 'MaliParser.prototype.maliDDKEvent.bind(this)'
        elif 'tracing_mark_write:log' == eventName:
            eventName = 'GestureParser.prototype.logEvent.bind(this)'
        elif 'tracing_mark_write:SyncInterpret' == eventName:
            eventName = 'GestureParser.prototype.syncEvent.bind(this)'
        elif 'tracing_mark_write:HandleTimer' == eventName:
            eventName = 'GestureParser.prototype.timerEvent.bind(this)'
        elif 'tracing_mark_write:android' == eventName:
            eventName = 'AndroidParser.prototype.traceMarkWriteAndroidEvent.bind(this)'
        elif 'tracing_mark_write' == eventName:
            eventName = 'FTraceImporter.prototype.traceMarkingWriteEvent_.bind(this)'
        elif 'tracing_mark_write:trace_event_clock_sync' == eventName:
            eventName = 'xxx'

    def parseHrtimerEvent(self, eventName: str, details: str):
        if 'hrtimer_cancel' == eventName:
            eventName = 'xx'
        elif 'hrtimer_expire_entry' == eventName:
            eventName = 'xx'
        elif 'hrtimer_expire_exit' == eventName:
            eventName = 'xx'
        elif 'hrtimer_init' == eventName:
            eventName = 'xx'
        elif 'hrtimer_start' == eventName:
            eventName = 'xx'

    def parseTimerEvent(self, eventName: str, details: str):
        if 'timer_expire_entry' == eventName:
            eventName = 'xx'
        elif 'timer_expire_exit' == eventName:
            eventName = 'xx'

    def parseMmEvent(self, eventName: str, details: str):
        if 'mm_vmscan_kswapd_wake' == eventName:
            eventName = 'MemReclaimParser.prototype.kswapdWake.bind(this)'
        elif 'mm_vmscan_kswapd_sleep' == eventName:
            eventName = 'MemReclaimParser.prototype.kswapdSleep.bind(this)'
        elif 'mm_vmscan_direct_reclaim_begin' == eventName:
            eventName = 'MemReclaimParser.prototype.reclaimBegin.bind(this)'
        elif 'mm_vmscan_direct_reclaim_end' == eventName:
            eventName = 'MemReclaimParser.prototype.reclaimEnd.bind(this)'
        elif 'mm_filemap_add_to_page_cache' == eventName:
            eventName = 'xx'
        elif 'mm_filemap_delete_from_page_cache' == eventName:
            eventName = 'xx'

    def parseWorkqueueEvent(self, eventName: str, details: str):
        if 'workqueue_execute_start' == eventName:
            eventName = 'WorkqueueParser.prototype.executeStartEvent.bind(this)'
        elif 'workqueue_execute_end' == eventName:
            eventName = 'WorkqueueParser.prototype.executeEndEvent.bind(this)'
        elif 'workqueue_queue_work' == eventName:
            eventName = 'WorkqueueParser.prototype.executeQueueWork.bind(this)'
        elif 'workqueue_activate_work' == eventName:
            eventName = 'WorkqueueParser.prototype.executeActivateWork.bind(this)'

    def parseIrqEvent(self, eventName: str, details: str):
        if 'irq_handler_entry' == eventName:
            eventName = 'IrqParser.prototype.irqHandlerEntryEvent.bind(this)'
        elif 'irq_handler_exit' == eventName:
            eventName = 'IrqParser.prototype.irqHandlerExitEvent.bind(this)'
        elif 'irq_disable' == eventName:
            eventName = 'IrqParser.prototype.irqoffStartEvent.bind(this)'
        elif 'irq_enable' == eventName:
            eventName = 'IrqParser.prototype.irqoffEndEvent.bind(this)'

    def parseSoftirqEvent(self, eventName: str, details: str):
        if 'softirq_raise' == eventName:
            eventName = 'IrqParser.prototype.softirqRaiseEvent.bind(this)'
        elif 'softirq_entry' == eventName:
            eventName = 'IrqParser.prototype.softirqEntryEvent.bind(this)'
        elif 'softirq_exit' == eventName:
            eventName = 'IrqParser.prototype.softirqExitEvent.bind(this)'

    def parseCpuEvent(self, eventName: str, details: str):
        if 'cpu_frequency' == eventName:
            eventName = 'PowerParser.prototype.cpuFrequencyEvent.bind(this)'
        elif 'cpu_frequency_limits' == eventName:
            eventName = 'PowerParser.prototype.cpuFrequencyLimitsEvent.bind(this)'
        elif 'cpu_idle' == eventName:
            eventName = 'PowerParser.prototype.cpuIdleEvent.bind(this)'

    def parseMaliEvent(self, eventName: str, details: str):
        if 'mali_dvfs_event' == eventName:
            eventName = 'MaliParser.prototype.dvfsEventEvent.bind(this)'
        elif 'mali_dvfs_set_clock' == eventName:
            eventName = 'MaliParser.prototype.dvfsSetClockEvent.bind(this)'
        elif 'mali_dvfs_set_voltage' == eventName:
            eventName = 'MaliParser.prototype.dvfsSetVoltageEvent.bind(this)'
        elif 'mali_job_systrace_event_start' == eventName:
            eventName = 'MaliParser.prototype.maliJobEvent.bind(this)'
        elif 'mali_job_systrace_event_stop' == eventName:
            eventName = ',MaliParser.prototype.maliJobEvent.bind(this)'

    def parseDmaEvent(self, eventName: str, details: str):
        if 'dma_fence_destroy' == eventName:
            eventName = 'xx'
        elif 'dma_fence_enable_signal' == eventName:
            eventName = 'xx'
        elif 'dma_fence_init' == eventName:
            eventName = 'xx'
        elif 'dma_fence_signaled' == eventName:
            eventName = 'xx'

    def parseSdeEvent(self, eventName: str, details: str):
        if 'sde_evtlog' == eventName:
            eventName = 'xx'
        elif 'sde_perf_calc_crtc' == eventName:
            eventName = 'xx'
        elif 'sde_perf_crtc_update' == eventName:
            eventName = 'xx'
        elif 'sde_perf_update_bus' == eventName:
            eventName = 'xx'
        elif 'sde_perf_set_danger_luts' == eventName:
            eventName = 'xx'
        elif 'sde_perf_set_qos_luts' == eventName:
            eventName = 'xx'

    def parseCgroupEvent(self, eventName: str, details: str):
        if 'cgroup_attach_task' == eventName:
            eventName = 'xx'
        elif 'cgroup_release' == eventName:
            eventName = 'xx'
        elif 'cgroup_rmdir' == eventName:
            eventName = 'xx'

    def parseTaskEvent(self, eventName: str, details: str):
        if 'task_newtask' == eventName:
            eventName = 'xx'
        elif 'task_rename' == eventName:
            eventName = 'xx'

    def parseBlockEvent(self, eventName: str, details: str):
        if 'block_rq_issue' == eventName:
            eventName = 'DiskParser.prototype.blockRqIssueEvent.bind(this)'
        elif 'block_rq_complete' == eventName:
            eventName = 'DiskParser.prototype.blockRqCompleteEvent.bind(this)'

    def parsePowerEvent(self, eventName: str, details: str):
        if 'power_start' == eventName:
            eventName = 'PowerParser.prototype.powerStartEvent.bind(this)'
        elif 'power_frequency' == eventName:
            eventName = 'PowerParser.prototype.powerFrequencyEvent.bind(this)'

    def parseSyncEvent(self, eventName: str, details: str):
        if 'sync_timeline' == eventName:
            eventName = 'SyncParser.prototype.timelineEvent.bind(this)'
        elif 'sync_wait' == eventName:
            eventName = 'SyncParser.prototype.syncWaitEvent.bind(this)'
        elif 'sync_pt' == eventName:
            eventName = 'SyncParser.prototype.syncPtEvent.bind(this)'

    def parseZeroEvent(self, eventName: str, details: str):
        if '0' == eventName:
            eventName = 'FTraceImporter.prototype.traceMarkingWriteEvent_.bind(this)'
        elif '0:android' == eventName:
            eventName = 'AndroidParser.prototype.traceMarkWriteAndroidEvent.bind(this)'
        elif '0:trace_event_clock_sync' == eventName:
            eventName = 'xxx'

    def parseGraphEvent(self, eventName: str, details: str):
        if 'graph_ent' == eventName:
            eventName = 'KernelFuncParser.prototype.traceKernelFuncEnterEvent.bind(this)'
        elif 'graph_ret' == eventName:
            eventName = 'KernelFuncParser.prototype.traceKernelFuncReturnEvent.bind(this)'

    def parsePreemptEvent(self, eventName: str, details: str):
        if 'preempt_disable' == eventName:
            eventName = 'IrqParser.prototype.preemptStartEvent.bind(this)'
        elif 'preempt_enable' == eventName:
            eventName = 'IrqParser.prototype.preemptEndEvent.bind(this)'

    def parseIpiEvent(self, eventName: str, details: str):
        if 'ipi_entry' == eventName:
            eventName = 'IrqParser.prototype.ipiEntryEvent.bind(this)'
        elif 'ipi_exit' == eventName:
            eventName = 'IrqParser.prototype.ipiExitEvent.bind(this)'

    def parseDefaultEvent(self, eventName:str, details):
        if 'kEventTraceHeaderOpcode' == eventName:
            eventName = 'EventTraceParser.prototype.decodeHeader.bind(this)'
        elif 'opcode' == eventName:
            eventName = 'xxx'
        elif 'memory_bus_usage' == eventName:
            eventName = 'BusParser.prototype.traceMarkWriteBusEvent.bind(this)'
        elif 'drm_vblank_event' == eventName:
            eventName = 'DrmParser.prototype.vblankEvent.bind(this)'
        elif 'intel_gpu_freq_change' == eventName:
            eventName = 'I915Parser.prototype.gpuFrequency.bind(this)'
        elif 'lowmemory_kill' == eventName:
            eventName = 'MemReclaimParser.prototype.lowmemoryKill.bind(this)'
        elif 'oom_score_adj_update' == eventName:
            eventName = 'xx'
        elif 'rpmh_send_msg' == eventName:
            eventName = 'xx'
        elif 'hwcEventName' == eventName:
            eventName = 'xx'
        else:
            print("tag={}  ###  action={}".format(eventName, details))
            if not eventName in UN_REGISTER_MAP:
                UN_REGISTER_MAP.append(eventName)

class SystemTrace:
    def __init__(self, trace_html:str):
        self.traceHtml = trace_html
        self.lines:TraceLine = []
        #{'key_pid':{key_tgid:TraceLine}}
        self.pidTraceDict = dict()
        if not isfile(trace_html) or not trace_html.endswith('.html'):
            self.isTraceFile = False
        else:
            self.isTraceFile = True
        self.initOther()

    def initOther(self):
        self.schedSwitchs = []
        self.schedWakeups = []
        self.schedWakings = []

    def parseLine(self, line:str):
        match = re.match(TraceLine.PATTERN_LINE, line)
        if match:
            #name or ... or idle 名称
            task:str = match.group(1).strip()
            #pid 进程id
            try:
                pid:int = int(match.group(2).strip())
            except :
                pid: int = 0
            #tgid 线程id
            try:
                tgid:int = int(match.group(3).strip())
            except :
                tgid: int = -1
                #cpuId 使用的cpu号
            try:
                cpuId:int = int(match.group(4).strip())
            except :
                cpuId: int = 0
            #irqs-off 终端请求了 [dX.]'d '表示中断被 disabled 。' .'表示中断没有关闭；
            irqsOff:str = str(match.group(5).strip())
            #need-resched 需要resched [Nnp.] 'N'表示 need_resched 被设置,'.'表示 need-reched 没有被设置，中断返回不会进行进程切换；
            needResched:str = str(match.group(6).strip())
            #hardirq/softirq 中断[Hhs.] 'H' 在 softirq 中发生了硬件中断, 'h' – 硬件中断，'s'表示 softirq，'.'不在中断上下文中，普通状态。
            irq:str = str(match.group(7).strip())
            #preempt-depth 优先等级[0-9a-f.] 当抢占中断使能后,该域代表 preempt_disabled 的级别
            preemptDepth:str = str(match.group(8).strip())
            #TIMESTAMP 时间戳
            timestamp:float = float(match.group(9).strip())
            #eventName
            eventName = match.group(10).strip()
            #details
            details = match.group(11).strip()
            return TraceLine(task, pid, tgid, cpuId, irqsOff, needResched, irq, preemptDepth, timestamp, eventName, details, self)
        else:
            return None

    def __addTraceLine__(self, line:TraceLine):
        self.lines.append(line)
        pidKey = 'key_{}'.format(line.pid)

        if pidKey in self.pidTraceDict.keys():
            pidTrace = self.pidTraceDict[pidKey]
        else:
            pidTrace = dict()
            self.pidTraceDict[pidKey] = pidTrace

        tgidKey = 'key_{}'.format(line.tgid)

        if tgidKey in pidTrace.keys():
            tgidList =pidTrace[tgidKey]
        else:
            tgidList = list()
            pidTrace[tgidKey] = tgidList
        tgidList.append(line)



    def parseTrace(self):
        if self.isTraceFile:
            beginTrace = False
            with open(self.traceHtml, encoding=toolUtils.checkFileCode(self.traceHtml)) as mFile:
                linenum = 0
                while True:
                    linenum = linenum+1
                    line = mFile.readline()
                    if not line:
                        break
                    elif '<!-- BEGIN TRACE -->' in line:
                        beginTrace = True
                    elif '<!-- END TRACE -->' in line:
                        beginTrace = False
                    elif beginTrace:
                        temp:TraceLine = self.parseLine(line)
                        if temp:
                            self.__addTraceLine__(temp)
                            # if temp.detail.test:
                            #     print(line)
                        else:
                            print(line.strip())

            UN_REGISTER_MAP.sort()
            print('UN_REGISTER_MAP = {}'.format(UN_REGISTER_MAP))
            print('pidTraceDict = {}'.format(self.pidTraceDict.keys()))


def test():
    PATTERN_LINE = '^[\s]*(.+)-([\d]+)[\s]+\(([\d|-|\s]+)\)[\s]+\[([\d]+)\][\s]+([d|X|\.])([N|n|p|\.])([H|h|s|\.])([0-9|a-f|\.])[\s]+([\d]+\.[\d]+):\s+([\S]+):\s(.*)$'
    PATTERN_LINE = '^[\s]*(.+)-([\d]+)[\s]+\(([^\s]+)\)[\s]+\[([\d]+)\][\s]+([d|X|\.])([N|n|p|\.])([H|h|s|\.])([0-9|a-f|\.])[\s]+([\d]+\.[\d]+):\s+([\S]+):\s(.*)$'
    PATTERN_LINE = '^[\s]*(.+)-([\d]+)[\s]+\(([^\)]+)\)[\s]+\[([\d]+)\][\s]+([d|X|\.])([N|n|p|\.])([H|h|s|\.])([0-9|a-f|\.])[\s]+([\d]+\.[\d]+):\s+([\S]+):\s(.*)$'
    line = '          <idle>-0     (-----) [007] dn.2  5680.980692: hrtimer_start: hrtimer=00000000fca38243 function=tick_sched_timer expires=5680990000000 softexpires=5680990000000'
    match = re.match(PATTERN_LINE, line)
    if match:
        print(match.groups())
    exit(0)

if __name__ == '__main__':
    #test()
    '''    
    #                                      _-----=> irqs-off
    #                                     / _----=> need-resched
    #                                    | / _---=> hardirq/softirq
    #                                    || / _--=> preempt-depth
    #                                    ||| /     delay
    #           TASK-PID    TGID   CPU#  ||||    TIMESTAMP  FUNCTION
    #              | |        |      |   ||||       |         |
              <idle>-0     (-----) [002] dn.1  1507.655129: cpu_pred_hist: idx:0 resi:13 sample:4 tmr:0
    '''
    trace_html = '''C:/Users/Administrator/trace.html'''
    trace = SystemTrace(trace_html)
    trace.parseTrace()