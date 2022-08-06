import pygame

class PygameAudioPlayer(object):
    def __init__(self):
        self.initiated = False
        self.current_sfx = None
        self.current_fn = None
        self.loop = False
        self.display = None
        self.volume = 1.0
        self.current_position = 0  # In milliseconds
        self.duration = 0  # In milliseconds
        self.next_pos = 0  # In seconds

    def initiate(self):
        pygame.mixer.pre_init(44100, -16, 2, 128 * 2**2)
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.set_volume(self.volume)
        self.display = pygame.display.set_mode((1, 1), pygame.NOFRAME)
        self.initiated = True
        pygame.display.iconify()

    def get_length(self):
        if self.current_sfx:
            return self.current_sfx.get_length() * 1000
        else:
            return 0

    def find_length(self, sfx):
        if not self.initiated:
            self.initiate()
        self.current_sfx = pygame.mixer.Sound(sfx.full_path)
        return self.current_sfx.get_length()  # Seconds

    def play(self, fn, loop=False):
        """
        Returns whether the song was actually re-loaded or just unpaused
        """
        if not self.initiated:
            self.initiate()
        self.loop = loop
        print("Play %s" % fn)
        if self.current_fn != fn:
            pygame.mixer.music.load(fn)
            self.current_sfx = pygame.mixer.Sound(fn)
            self.duration = self.current_sfx.get_length() * 1000
            pygame.mixer.music.set_volume(self.volume)
            if self.loop:
                pygame.mixer.music.play(-1)
            else:
                pygame.mixer.music.play(0)
            self.current_fn = fn
            self.current_position = 0
            print(fn, self.duration)
            return True
        else:
            self.unpause()
            return False

    def pause(self):
        if not self.initiated:
            self.initiate()
        self.next_pos = self.get_position() / 1000.
        self.current_position = self.get_position()
        pygame.mixer.music.stop()

    def unpause(self):
        print("Unpause")
        if self.loop:
            pygame.mixer.music.play(-1, self.next_pos)
        else:
            pygame.mixer.music.play(0, self.next_pos)

    def stop(self):
        if self.initiated:
            pygame.mixer.music.stop()
            self.current_position = 0
            self.next_pos = 0
            self.current_sfx = None
            self.current_fn = None
            self.duration = 0

    def quit(self):
        if self.initiated:
            self.initiated = False
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            pygame.quit()

    def set_volume(self, vol):
        self.volume = vol

    def get_position(self):
        if self.initiated and self.current_sfx:
            cur_pos = pygame.mixer.music.get_pos()
            print(self.current_position, cur_pos)
            if cur_pos == -1:
                return -1
            return self.current_position + cur_pos
        else:
            return 0

    def preset_position(self):
        if self.current_sfx:
            pygame.mixer.music.stop()

    def set_position(self, val):
        if self.current_sfx:
            print("Set Position: %s" % val)
            # Must stop and restart in order to
            # preserve get position working correctly
            # pygame.mixer.music.stop()
            self.next_pos = val / 1000.
            self.current_position = val

    def get_time(self):
        return pygame.get_time()

PLAYER = None
def get_player():
    global PLAYER
    if not PLAYER:
        PLAYER = PygameAudioPlayer()
    return PLAYER
