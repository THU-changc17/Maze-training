import sys
import os
if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5 import QtWidgets,QtGui,QtCore
from MazeDialog import Ui_Maze
from stop_thread import Stop_th
import random
import time
import threading


class MazeForm(QtWidgets.QDialog,Ui_Maze):
    def __init__(self):
        super(MazeForm,self).__init__()
        self.setupUi(self)
        self.setWindowTitle("迷宫寻蛋糕")
        self.setWindowIcon(QtGui.QIcon('myico.ico'))
        palette = QtGui.QPalette()
        #pix = QtGui.QPixmap("tim.jpg")
        #pix = pix.scaled(self.width(), self.height())
        #palette.setBrush(QtGui.QPalette.Background, QtGui.QBrush(pix))
        palette.setColor(self.backgroundRole(), QtGui.QColor(255, 255, 255))
        self.setPalette(palette)

        #self.tableWidget.setFrameShape(0)
        #self.tableWidget.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableWidget.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableWidget.setRowCount(6)
        self.tableWidget.setColumnCount(6)
        #self.tableWidget.setHorizontalHeaderLabels(['文件名'])
        self.tableWidget.verticalHeader().setHidden(True)
        self.tableWidget.horizontalHeader().setHidden(True)
        self.getmaze.clicked.connect(self.newmaze)
        self.startlearn.clicked.connect(self.looplearn)
        self.search.clicked.connect(self.start_Search)
        self.clip_list = []
        self.alpha = 0.1
        self.gamma = 0.9
        self.epoch = 100
        self.epsilon = 0.8
        self.ismaze = 0
        #self.isfire = 0
        self.fire_make = threading.Thread(target=self.update_fire)
        self.fire_thread = 0
        self.learning = 0
        self.searching = 0
        #self.update.start()
        self.state_Signal.connect(self.changeui)
        self.fire_Signal.connect(self.change_fireui)

    state_Signal = QtCore.pyqtSignal(int,int)
    fire_Signal = QtCore.pyqtSignal(int)

    def closeEvent(self,event):
        os._exit(0)

#每行0 1 2 3分别为每个状态向上、下、左、右移动,有火焰和无火焰的Qtable不同
    def newmaze(self):
        if (self.learning == 1):
            QtWidgets.QMessageBox.about(self, "提示", "正在学习中...")
        elif (self.searching == 1):
            QtWidgets.QMessageBox.about(self, "提示", "正在寻找中...")
        else:
            self.label.setText("")
            if (self.fire_thread == 1):  #关闭之前的火线程
                Stop_th(self.fire_make)
                self.fire_thread = 0
            self.tableWidget.clear()
            self.ranknum = int(self.spinBox.text())
            wall_num = 0
            self.clip_list = []
            self.fire_list = []
            # self.Qtable_fire = [[0 for i in range(4)] for i in range(self.ranknum * self.ranknum * 2)]
            if (self.fire.isChecked()):
                self.state = [i for i in range(self.ranknum * self.ranknum * 2)]
                self.Qtable = [[0 for i in range(5)] for i in range(self.ranknum * self.ranknum * 2)]
            else:
                self.state = [i for i in range(self.ranknum * self.ranknum)]
                self.Qtable = [[0 for i in range(5)] for i in range(self.ranknum * self.ranknum)]
            # self.state_fire = [i for i in range(self.ranknum * self.ranknum * 2)]
            if (self.ranknum < 6 or self.ranknum > 10):
                QtWidgets.QMessageBox.about(self, "提示", "请选择6到10阶的迷宫阶数")
            else:
                self.tableWidget.setRowCount(self.ranknum)
                self.tableWidget.setColumnCount(self.ranknum)
                # maze_array = np.zeros((self.ranknum,self.ranknum))
                self.rewards = [0] * self.ranknum * self.ranknum  #无火焰rewards
                self.rewards_fire = [0] * self.ranknum * self.ranknum * 2   #有火焰rewards
                clip_num = 0
                fire_num = 0
                if (self.easy.isChecked()):
                    wall_num = self.ranknum * self.ranknum // 6
                    clip_num = 1
                    fire_num = 3
                elif (self.medium.isChecked()):
                    wall_num = self.ranknum * self.ranknum // 5
                    clip_num = 2
                    fire_num = 4
                elif (self.hard.isChecked()):
                    wall_num = self.ranknum * self.ranknum // 4
                    clip_num = 3
                    if (self.ranknum < 8):
                        fire_num = 3
                    else:
                        fire_num = 7
                if (self.trap.isChecked() is False):
                    clip_num = 0
                if (self.fire.isChecked() is False):
                    fire_num = 0
                ran = [i for i in range(1, self.ranknum * self.ranknum - 1)]
                wall_list = random.sample(ran, wall_num)
                for i in wall_list:
                    self.tableWidget.setItem(i // self.ranknum, i % self.ranknum, QtWidgets.QTableWidgetItem(""))
                    self.tableWidget.item(i // self.ranknum, i % self.ranknum).setBackground(
                        QtGui.QBrush(QtGui.QColor(0, 0, 0)))
                    self.rewards[i] = -10
                    self.rewards_fire[i] = -10
                    self.rewards_fire[i + self.ranknum * self.ranknum] = -10
                    # self.rewards_fire[i] = -10
                clip_ran = list(set(j for j in range(1, self.ranknum * self.ranknum - 1)) - set(wall_list))
                self.clip_list = random.sample(clip_ran, clip_num)
                fire_ran = list(set(clip_ran) - set(self.clip_list))
                if (1 in fire_ran):
                    fire_ran.remove(1)
                if (self.ranknum in fire_ran):
                    fire_ran.remove(self.ranknum)
                fire_discrete = 0   #不生成连续型火焰
                while (fire_discrete == 0):
                    self.fire_list = random.sample(fire_ran, fire_num)
                    # print(self.fire_list)
                    judge_discrete = 0
                    for h in self.fire_list:
                        if ((h + 1) in self.fire_list or (h - 1) in self.fire_list
                                or (h - self.ranknum) in self.fire_list or (h + self.ranknum) in self.fire_list):
                            judge_discrete = 1
                    if (judge_discrete == 1):
                        fire_discrete = 0
                    else:
                        fire_discrete = 1
                for j in self.clip_list:
                    self.tableWidget.setItem(j // self.ranknum, j % self.ranknum, QtWidgets.QTableWidgetItem(""))
                    clip_pic = QtWidgets.QLabel()
                    clip_pic.setPixmap(QtGui.QPixmap("kill.ico"))
                    self.tableWidget.setCellWidget(j // self.ranknum, j % self.ranknum, clip_pic)
                    self.rewards[j] = -30
                    self.rewards_fire[j] = -30
                    self.rewards_fire[j + self.ranknum * self.ranknum] = -30
                    # self.rewards_fire[j] = -30
                self.rewards_fire[-1] = 10
                self.rewards_fire[self.ranknum * self.ranknum - 1] = 10
                self.rewards[-1] = 10   #定义rewards
                # self.rewards_fire[-1] = 10
                for l in self.fire_list:  #只有n之后的fire reward为-10
                    self.rewards_fire[l + self.ranknum * self.ranknum] = -10
                if (len(self.fire_list) != 0):
                    self.fire_make = threading.Thread(target=self.update_fire)
                    self.fire_make.start()
                    self.fire_thread = 1
                # self.tableWidget.setCellWidget(0, 0, self.rat_pic)
                # self.tableWidget.removeCellWidget(0,0)
                rat_pic = QtWidgets.QLabel()
                rat_pic.setPixmap(QtGui.QPixmap("rat.ico"))
                food_pic = QtWidgets.QLabel()
                food_pic.setPixmap(QtGui.QPixmap("food.ico"))
                self.tableWidget.setCellWidget(0, 0, rat_pic)
                self.tableWidget.setCellWidget(self.ranknum - 1, self.ranknum - 1, food_pic)
                self.ismaze = 1
#取列表中所有最大值序号函数
    def get_maxpos(self,list):
        element = max(list)
        count = list.count(element)
        pos = []
        y = 0
        for p in range(count):
            list_tmp = list[y:]
            y += list_tmp.index(element) + 1
            pos.append(y - 1)
        return pos
#宽度优先判断迷宫有解
    def judge(self):
        start_p = 0
        checked_list = []
        checked_list.append(start_p)
        for i in checked_list:
            #print(checked_list)
            if (i - self.ranknum >= 0 and i - self.ranknum <= self.ranknum * self.ranknum - 1
                    and self.rewards[i - self.ranknum] >= 0 and (i - self.ranknum) not in checked_list):
                checked_list.append(i - self.ranknum)
            if (i + self.ranknum >= 0 and i + self.ranknum <= self.ranknum * self.ranknum - 1
                    and self.rewards[i + self.ranknum] >= 0 and (i + self.ranknum) not in checked_list):
                checked_list.append(i + self.ranknum)
            if (i % self.ranknum != 0 and i - 1 <= self.ranknum * self.ranknum - 1
                    and self.rewards[i - 1] >= 0 and (i - 1) not in checked_list):
                checked_list.append(i - 1)
            if (i % self.ranknum != self.ranknum - 1 and i + 1 <= self.ranknum * self.ranknum - 1
                    and self.rewards[i + 1] >= 0 and (i + 1) not in checked_list):
                checked_list.append(i + 1)
        if(self.ranknum * self.ranknum - 1 in checked_list):
            return True
        else:
            return False
#更新行动价值表
    def updateQ(self,curr,action,next):
        #if(next == curr):
        #    next_reward = -10
        if(self.fire.isChecked()):
            next_reward = self.rewards_fire[next]
        else:
            next_reward = self.rewards[next]
        self.Qtable[curr][action] = (1 - self.alpha) * self.Qtable[curr][action] \
                                        + self.alpha * (next_reward + self.gamma * max(self.Qtable[next]))

    # def updateQ_fire(self,curr,action,next):
    #     next_reward = self.rewards_fire[next]
    #     #if(next == curr):
    #     #    next_reward = -10
    #     self.Qtable_fire[curr][action] = (1 - self.alpha) * self.Qtable_fire[curr][action]\
    #                                 + self.alpha * (next_reward + self.gamma * max(self.Qtable_fire[next]))
#开始学习
    def looplearn(self):
        if(self.learning == 1):
            QtWidgets.QMessageBox.about(self, "提示", "正在学习中...")
        elif(self.searching == 1):
            QtWidgets.QMessageBox.about(self, "提示", "正在寻找中...")
        elif(self.ismaze == 0):
            QtWidgets.QMessageBox.about(self, "提示", "请先生成迷宫!")
        elif(self.judge() == False):
            QtWidgets.QMessageBox.about(self, "提示", "此迷宫不可解！")
        else:
            rat_pic = QtWidgets.QLabel()
            rat_pic.setPixmap(QtGui.QPixmap("rat.ico"))
            food_pic = QtWidgets.QLabel()
            food_pic.setPixmap(QtGui.QPixmap("food.ico"))
            self.tableWidget.setCellWidget(0, 0, rat_pic)
            self.tableWidget.setCellWidget(self.ranknum - 1, self.ranknum - 1, food_pic)
            # print('learning...')
            self.update_learn = threading.Thread(target=self.update_learnui)
            self.update_learn.start()
#新建线程
    def update_learnui(self):
        self.learning = 1
        self.epoch = int(self.epo.text())
        last_emited = 0
        for k in range(self.epoch):
            curr_state = self.state[0]
            self.label.setText("Epoch"+" "+str(k)+" "+"learning")
            while (curr_state != self.state[-1] and curr_state!= self.state[self.ranknum * self.ranknum - 1]):
                action_choice = [0,1,2,3,4]
                if (curr_state // self.ranknum == 0 or curr_state // self.ranknum == self.ranknum):
                    action_choice.remove(0)
                if (curr_state // self.ranknum == self.ranknum - 1 or curr_state // self.ranknum == self.ranknum * 2 - 1):
                    action_choice.remove(1)
                if (curr_state % self.ranknum == 0):
                    action_choice.remove(2)
                if (curr_state % self.ranknum == self.ranknum - 1):
                    action_choice.remove(3)
                if (random.uniform(0, 1) > self.epsilon):
                    action = random.choice(action_choice)
                else:
                    action_list = [self.Qtable[curr_state][j] for j in action_choice]
                    action = action_choice[random.choice(self.get_maxpos(action_list))]
                #print(action_choice)
                if (action == 0 and curr_state // self.ranknum != 0 and curr_state // self.ranknum != self.ranknum):
                    next_state = curr_state - self.ranknum
                elif (action == 1 and curr_state // self.ranknum != self.ranknum - 1
                      and curr_state // self.ranknum != self.ranknum * 2 -1):
                    next_state = curr_state + self.ranknum
                elif (action == 2 and curr_state % self.ranknum != 0):
                    next_state = curr_state - 1
                elif (action == 3 and curr_state % self.ranknum != self.ranknum - 1):
                    next_state = curr_state + 1
                else:
                    next_state = curr_state
                if(self.fire.isChecked()):
                    if (curr_state < self.ranknum * self.ranknum):
                        next_state = next_state + self.ranknum * self.ranknum
                    else:
                        next_state = next_state - self.ranknum * self.ranknum
                # print(next_state[i])
                #print(str(curr_state) + "+" + str(next_state))
                #if(k%2 == 0):
                self.updateQ(curr_state, action, next_state)
                #else:
                #   self.updateQ_fire(curr_state, action, next_state)
                if(self.eye.isChecked()):  #勾选学习动画
                    if(curr_state < self.ranknum * self.ranknum):
                        emited_curr = curr_state
                    else:
                        emited_curr = curr_state - self.ranknum * self.ranknum
                    if (next_state < self.ranknum * self.ranknum):
                        emited_next = next_state
                    else:
                        emited_next = next_state - self.ranknum * self.ranknum
                    self.state_Signal.emit(emited_curr, emited_next)
                    last_emited = emited_next
                    #print(last_emited)
                    time.sleep(0.01)
                curr_state = next_state
        self.label.setText("learned")
        self.state_Signal.emit(last_emited,0)
        self.learning = 0
#开始寻找
    def start_Search(self):
        if (self.learning == 1):
            QtWidgets.QMessageBox.about(self, "提示", "正在学习中...")
        elif (self.searching == 1):
            QtWidgets.QMessageBox.about(self, "提示", "正在寻找中...")
        elif (self.ismaze == 0):
            QtWidgets.QMessageBox.about(self, "提示", "请先生成迷宫!")
        elif (self.judge() == False):
            QtWidgets.QMessageBox.about(self, "提示", "此迷宫不可解！")
        else:
            rat_pic = QtWidgets.QLabel()
            rat_pic.setPixmap(QtGui.QPixmap("rat.ico"))
            food_pic = QtWidgets.QLabel()
            food_pic.setPixmap(QtGui.QPixmap("food.ico"))
            self.tableWidget.setCellWidget(0, 0, rat_pic)
            self.tableWidget.setCellWidget(self.ranknum - 1, self.ranknum - 1, food_pic)
            if(self.fire_thread == 1):
                Stop_th(self.fire_make)
            if(self.fire.isChecked()):
                self.fire_make = threading.Thread(target=self.update_fire)
                self.fire_make.start()
                self.fire_thread = 1
            self.update_search = threading.Thread(target=self.update_searchui)
            self.update_search.start()
#新建寻找线程
    def update_searchui(self):
        self.searching = 1
        curr_state = self.state[0]
        self.label.setText("Searching")
        num = 0
        while (curr_state != self.state[-1] and curr_state not in self.clip_list and curr_state!= self.state[self.ranknum * self.ranknum - 1]):
            action_choice = [0, 1, 2, 3, 4]
            if (curr_state // self.ranknum == 0 or curr_state // self.ranknum == self.ranknum):
                action_choice.remove(0)
            if (curr_state // self.ranknum == self.ranknum - 1 or curr_state // self.ranknum == self.ranknum * 2 - 1):
                action_choice.remove(1)
            if (curr_state % self.ranknum == 0):
                action_choice.remove(2)
            if (curr_state % self.ranknum == self.ranknum - 1):
                action_choice.remove(3)
            action_list = [self.Qtable[curr_state][j] for j in action_choice]
            action = action_choice[random.choice(self.get_maxpos(action_list))]
            print(action_choice)
            if (action == 0 and curr_state // self.ranknum != 0 and curr_state // self.ranknum != self.ranknum):
                next_state = curr_state - self.ranknum
            elif (action == 1 and curr_state // self.ranknum != self.ranknum - 1
                  and curr_state // self.ranknum != self.ranknum * 2 - 1):
                next_state = curr_state + self.ranknum
            elif (action == 2 and curr_state % self.ranknum != 0):
                next_state = curr_state - 1
            elif (action == 3 and curr_state % self.ranknum != self.ranknum - 1):
                next_state = curr_state + 1
            else:
                next_state = curr_state
            if (self.fire.isChecked()):
                if (curr_state < self.ranknum * self.ranknum):
                    next_state = next_state + self.ranknum * self.ranknum
                else:
                    next_state = next_state - self.ranknum * self.ranknum
            # if(self.fire.isChecked() and next_state in self.fire_list and self.isfire == 1):
            #     next_state = curr_state
                # print(next_state[i])
            print(str(curr_state) + "+" + str(next_state))
            if (curr_state < self.ranknum * self.ranknum):
                emited_curr = curr_state
            else:
                emited_curr = curr_state - self.ranknum * self.ranknum
            if (next_state < self.ranknum * self.ranknum):
                emited_next = next_state
            else:
                emited_next = next_state - self.ranknum * self.ranknum
            self.state_Signal.emit(emited_curr, emited_next)
            #self.state_Signal.emit(curr_state, next_state)
            curr_state = next_state
            time.sleep(0.5)
        if(curr_state in self.clip_list):
            self.label.setText("Dead...")
        else:
            self.label.setText("Congratulations!!!")
            if (curr_state < self.ranknum * self.ranknum):
                emited_curr = curr_state
            else:
                emited_curr = curr_state - self.ranknum * self.ranknum
            self.state_Signal.emit(emited_curr, emited_curr)
        self.searching = 0
#接受信号更新界面
    def changeui(self,rev_curr,rev_next):
        #print(str(rev_curr) + "#" + str(rev_next))
        #if(curr!=next):
        if(rev_curr != self.state[-1] and rev_curr not in self.clip_list and rev_curr !=self.state[self.ranknum * self.ranknum - 1]):
            self.tableWidget.removeCellWidget(rev_curr // self.ranknum, rev_curr % self.ranknum)
        if(rev_next != self.state[-1] and rev_next not in self.clip_list and rev_next !=self.state[self.ranknum * self.ranknum - 1]):
            rat_pic = QtWidgets.QLabel()
            rat_pic.setPixmap(QtGui.QPixmap("rat.ico"))
            self.tableWidget.setCellWidget(rev_next // self.ranknum, rev_next % self.ranknum, rat_pic)
        if(rev_curr == rev_next and rev_curr == self.state[self.ranknum * self.ranknum - 1]):
            self.tableWidget.removeCellWidget(self.ranknum - 1, self.ranknum - 1)
            rat_pic = QtWidgets.QLabel()
            rat_pic.setPixmap(QtGui.QPixmap("rat.ico"))
            self.tableWidget.setCellWidget(rev_next // self.ranknum, rev_next % self.ranknum, rat_pic)
#生成周期性火焰
    def update_fire(self):
        i = 1
        while(1):
            if(i == 1):
                self.fire_Signal.emit(1)
                i = 0
                #self.isfire = 0
            else:
                self.fire_Signal.emit(0)
                i = 1
                #self.isfire = 1
            time.sleep(0.5)
#火焰生成ui
    def change_fireui(self,revint):
        if(revint == 0):
            for i in self.fire_list:
                self.tableWidget.removeCellWidget(i // self.ranknum, i % self.ranknum)
        else:
            for i in self.fire_list:
                fire_pic = QtWidgets.QLabel()
                fire_pic.setPixmap(QtGui.QPixmap("fire.ico"))
                self.tableWidget.setCellWidget(i // self.ranknum, i % self.ranknum, fire_pic)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    my_form = MazeForm()
    my_form.show()
    # my_form.setFixedSize(980,600)
    # my_form.use_palette()
    sys.exit(app.exec_())
