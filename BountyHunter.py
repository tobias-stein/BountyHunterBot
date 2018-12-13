import ctypes
import numpy as np
from matplotlib import pyplot as plt

# load dll
dll = ctypes.cdll.BountyHunterAI


class PlayerAction(ctypes.Structure):
    _fields_ = [
        ("move", ctypes.c_float),
        ("turn", ctypes.c_float)
    ]


class PlayerState(ctypes.Structure):
    _fields_ = [
        ("image", ctypes.c_void_p),
        ("playerPositionX", ctypes.c_float),
        ("playerPositionY", ctypes.c_float),
        ("playerRotation", ctypes.c_float),
        ("playerPocketLoad", ctypes.c_float),
        ("playerStashLoad", ctypes.c_float),
        ("playerDead", ctypes.c_bool),
        ("playerReward", ctypes.c_float),
    ]

class Game(object):
    def __init__(self, num_player):
        self.num_player = num_player
        self.player_id = []
        self.player_action = {}
        self.player_state = None
        self.player_actions_ptr = None
        self.frame_buffer = None

        # create
        dll.CreateNewGameInstance.argtypes = None
        dll.CreateNewGameInstance.restype = ctypes.c_void_p

        # initialize
        dll.InitializeGame.argtypes = [ctypes.c_void_p]
        dll.InitializeGame.restype = None

        # restart
        dll.RestartGame.argtypes = [ctypes.c_void_p]
        dll.RestartGame.restype = None

        # add player
        dll.AddPlayer.argtypes = [ctypes.c_void_p]
        dll.AddPlayer.restype = ctypes.c_size_t

        # step
        dll.StepGame.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(PlayerAction)), (PlayerState * num_player)]
        dll.StepGame.restype = None

        # terminate
        dll.TerminateGame.argtypes = [ctypes.c_void_p]
        dll.TerminateGame.restype = None

        # create a new game instance
        self.obj = dll.CreateNewGameInstance()

        # initialize the game
        dll.InitializeGame(self.obj)
        self.Restart()
        self.foo=True

    def Restart(self):
        dll.RestartGame(self.obj)

        self.player_id = []
        self.player_action = {}

        # re-join player
        for _ in range(self.num_player):
            pid = dll.AddPlayer(self.obj)
            self.player_id.append(pid)
            self.player_action[pid] = PlayerAction(20.0, 0.0)

        # PlayerActions** = (PlayerActions**)(new PlayerActions*[2] = { &player_one_action, &player_two_action});
        player_actions_arr = (ctypes.POINTER(PlayerAction) * self.num_player)(*[ctypes.pointer(self.player_action[self.player_id[i]]) for i in range(self.num_player)])
        self.player_actions_ptr = ctypes.cast(player_actions_arr, ctypes.POINTER(ctypes.POINTER(PlayerAction)))

    def Terminate(self):
        dll.TerminateGame(self.obj)

    def Step(self):
        # PlayerState[self.num_player]
        out_states = (PlayerState * self.num_player)()
        dll.StepGame(self.obj, self.player_actions_ptr, out_states)
        self.player_state = out_states

        if self.foo:
            arr_size = 768 * 768 * 3

            buf_from_mem = ctypes.pythonapi.PyMemoryView_FromMemory
            buf_from_mem.restype = ctypes.py_object
            buf_from_mem.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_int)

            #buffer = buf_from_mem(out_states[0].image, arr_size, 0x100)
            #self.frame_buffer = np.ndarray((768, 768, 3), np.byte, buffer).copy()

            ap = ctypes.cast(out_states[0].image, ctypes.POINTER(ctypes.c_ubyte * arr_size))
            #self.frame_buffer = np.frombuffer(ap.contents)
            buffer = buf_from_mem(ap.contents, arr_size, 0x100)
            self.frame_buffer =np.ndarray((768, 768, 3), np.byte, buffer)
            self.foo=False


    def DumpGameState(self):

        print("#Player |  Speed   Turn   | PositionX PositionY Rotation Pocket-Load Stash-Load Dead? Reward")
        print("------- + ------- ------- + --------- --------- -------- ----------- ---------- ----- ------")
        for i in range(self.num_player):

            pid = self.player_id[i]

            act = self.player_action[pid]

            mov = act.move
            trn = act.turn

            pst = self.player_state[pid]

            pos_x = pst.playerPositionX
            pos_y = pst.playerPositionY
            angle = pst.playerRotation
            pockt = pst.playerPocketLoad
            stash = pst.playerStashLoad
            death = pst.playerDead
            rewad = pst.playerReward

            print("{0:7d} | {1:7.2f} {2:7.2f} | {3:9.2f} {4:9.2f} {5:8.2f} {6:11.2f} {7:10.2f} {8:5s} {9:6.2f}".format(pid, mov, trn, pos_x, pos_y, angle, pockt, stash, "True" if death else "False", rewad))

    def RenderGameState(self):
        print(self.frame_buffer)
        #if self.frame_buffer is not None:
        #    plt.imshow(self.frame_buffer)
        #    plt.show()
