import time

import npyscreen
from epf import shm, constants


class Stats(npyscreen.NPSAppManaged):
    session = None
    def onStart(self):
        self.keypress_timeout_default = 10
        self.addForm("MAIN", MainForm, name="Evolutionary Protocol Fuzzer", lines=33, columns=106)

    def set_session(self, sess):
        self.session = sess


class BoxedStats(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit


class Info(npyscreen.BoxTitle):
    _contained_widget = npyscreen.FixedText


class MainForm(npyscreen.FormBaseNew):
    prev_iterations = 0

    def create(self):
        y, x = self.useable_space()
        self.add_handlers({"^Q": self.pause_handler})
        self.general = self.add(BoxedStats, name="General", max_height=8, max_width=x//2 - 2, editable=False)
        self.target = self.add(BoxedStats, name="Target Info", relx=x//2+1, rely=2, max_height=13, max_width=x // 2 - 2, editable=False)
        self.instrumentation = self.add(BoxedStats, name="Instrumentation", rely=10, max_height=7, max_width=x // 2 - 2, editable=False)
        self.genetics = self.add(BoxedStats, name="Evolutionary Engine", relx=x//2+1, rely=15, max_height=16, max_width=x // 2 - 2, editable=False)
        self.insight = self.add(BoxedStats, name="Active Population Queue", rely=17, max_height=11, max_width=x // 2 - 2, editable=False)
        self.add(npyscreen.Textfield, name="keepalive", relx=1, rely=1, max_height=2, max_width=2)
        self.info = self.add(Info, name="", rely=28, max_height=3, max_width=x//2-2)
        self.info.value = "ctrl+q -> pause and spawn cli"
        self.display()

    def pause_handler(self, _):
        self.parentApp.switchForm(None)

    def while_waiting(self):
        s = self.parentApp.session
        if s.active_individual is None:
            return
        its_per_sec = s.test_case_cnt - self.prev_iterations
        self.prev_iterations += its_per_sec
        self.general.value = f'Fuzzer:             {s.fuzz_protocol.name}\n' + \
                             f'Elapsed Time:       {round(s.time_budget.execution_time, 2)}/{round(s.time_budget.budget, 2)} [sec]\n' + \
                             f'Iterations per sec: {its_per_sec} [#/sec]\n' + \
                             f'Iterations total:   {s.test_case_cnt} [#]\n' + \
                             f'Random seed:        {s.opts.seed}\n' + \
                             f'Suspects found:     {0} [#]'
        self.target.value = f'Command:        {s._restarter._cmd}\n' + \
                            f'PID:            {s._restarter._pid}\n' + \
                            f'Protocol:       {s.target._target_connection.proto}\n' + \
                            f'Connection:     {s.target._target_connection.host}:{s.target._target_connection.port}\n' + \
                            f'Send timeout:   {s.opts.send_timeout} [sec]\n' + \
                            f'Recv timeout:   {s.opts.recv_timeout} [sec]\n' + \
                            f'Restarts:       {s._restarter.restarts} [#]\n' + \
                            f'Timeouts:       {s.target._target_connection.recv_timeout_count + s.target._target_connection.send_timeout_count} [#]\n' + \
                            f'Conn Errors:    {s.target._target_connection.conn_errors} [#]\n' + \
                            f'Crashes:        {s._restarter.crashes} [#]\n'
        mem = shm.get()
        uniq, _ = mem.directed_branch_coverage()
        self.instrumentation.value = f'Shared MMAP ID: {mem.name}\n' + \
                                     f'Injection ENV:  {constants.INSTR_AFL_ENV}\n' + \
                                     f'Memory size:    {mem.size / 1024} [kiB]\n' + \
                                     f'Reported cov.:  {uniq} [# block transitions]\n' + \
                                     f'Last cov. inc.: {round(time.time() - mem.tstamp, 2)} [sec]'
        self.genetics.value = f'Population seed:  {s.opts.pcap}\n' + \
                              f'Populations:      {len(s.populations)} [#]\n' + \
                              f'Alpha (Cooldown): {s.opts.alpha}\n' + \
                              f'Beta (Reheat):    {s.opts.beta}\n' + \
                              f'pMutation:        {s.active_population._p_mutation}\n' + \
                              f'Individual limit: {s.opts.population_limit} [#/population]\n' + \
                              f'Active Pop.:      {s.active_population.species}\n' + \
                              f'Active Indiv.:    {s.active_individual.identity}\n' + \
                              f'Individuals:      {len(s.active_population)} [#,active]\n' + \
                              f'Current Energy:   {s.energy}\n' + \
                              f'Crossovers:       {sum(p.crossovers for p in s.populations.values())} [#]\n' + \
                              f'Spot Mutations:   {sum(p.spot_mutations for p in s.populations.values())} [#]\n' + \
                              f'Reheats:          {s.reheat_count} [#]\n' + \
                              f'Energy Periods:   {s.energy_periods} [#]'
        head = s.active_population._pop[:3]
        tail = s.active_population._pop[-3:]
        self.insight.value = 'Highest priority individuals:\n' + \
                             f'      [0]  {head[0].identity}\n' + \
                             f'      [1]  {head[1].identity}\n' + \
                             f'      [2]  {head[2].identity}\n' + \
                             '             ... \n' + \
                             'Lowest priority individuals:\n' + \
                             f'     [n-3] {tail[0].identity}\n' + \
                             f'     [n-2] {tail[1].identity}\n' + \
                             f'     [n-1] {tail[2].identity}'
        self.display()



