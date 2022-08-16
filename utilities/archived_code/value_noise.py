import math, random
from app.map_maker.utilities import get_random_seed

class ValueNoise():
    num_octaves = 3
    pixels_per_lattice = 4
    starting_frequency = 1
    frequency_mult = 2  # lacunarity
    amplitude_mult = 0.5
    starting_amplitude = 1

    def __init__(self, width: int, height: int, seed: int):
        self.pixel_width = width
        self.pixel_height = height
        self.seed = seed
        random.seed(self.seed)
        self.lattice_width = width // self.pixels_per_lattice
        self.lattice_height = height // self.pixels_per_lattice

        self.noise_map = self.generate_full_noise_map()

    def generate_full_noise_map(self):
        true_noise_map = [0 for _ in range(self.pixel_width * self.pixel_height)]
        frequency = self.starting_frequency
        amplitude = self.starting_amplitude
        for i in range(self.num_octaves):
            # print("Octave: %d" % i)
            noise_map = self.generate_noise_map(frequency)
            noise_map = [v * amplitude for v in noise_map]
            amplitude *= self.amplitude_mult
            frequency *= self.frequency_mult
            true_noise_map = [n + tn for n, tn in zip(noise_map, true_noise_map)]
        # normalize map
        max_value = max(true_noise_map)
        min_value = min(true_noise_map)
        true_noise_map = [(v - min_value) / (max_value - min_value) for v in true_noise_map]
        return true_noise_map

    def _interp(self, a, b, t):
        # t should be in range 0 to 1
        remap_t = t * t * (3 - 2 * t)
        return a * (1 - remap_t) + b * remap_t

    def generate_noise_map(self, frequency):
        randoms = [random.random() for _ in range(self.lattice_width * self.lattice_height)]
        noise_map = []
        for px in range(self.pixel_width):
            for py in range(self.pixel_height):
                lx = px * frequency / self.pixels_per_lattice
                ly = py * frequency / self.pixels_per_lattice
                lx %= self.lattice_width
                ly %= self.lattice_height
                flx = math.floor(lx)
                fly = math.floor(ly)
                tx = lx - flx
                ty = ly - fly
                rx0 = flx
                rx1 = (flx + 1) % self.lattice_width
                ry0 = fly
                ry1 = (fly + 1) % self.lattice_height
                c00 = randoms[rx0 * self.lattice_height + ry0]
                c10 = randoms[rx0 * self.lattice_height + ry1]
                c01 = randoms[rx1 * self.lattice_height + ry0]
                c11 = randoms[rx1 * self.lattice_height + ry1]
                nx0 = self._interp(c00, c01, tx)
                nx1 = self._interp(c10, c11, tx)
                ny = self._interp(nx0, nx1, ty)
                noise_map.append(ny)
        return noise_map

    def get(self, x: int, y: int) -> float:
        x = x % self.pixel_width
        y = y % self.pixel_height
        noise_value = self.noise_map[x * self.pixel_height + y]
        return noise_value

class GrassValueNoise(ValueNoise):
    num_octaves = 3
    pixels_per_lattice = 4
    starting_frequency = 1
    frequency_mult = 2  # lacunarity
    amplitude_mult = 0.5
    starting_amplitude = 1

GRASSVALUENOISE = None

def get_grass_noise_map(width, height):
    global GRASSVALUENOISE
    new_width = 64 
    new_height = 64
    if GRASSVALUENOISE and GRASSVALUENOISE.pixel_width == new_width and GRASSVALUENOISE.pixel_height == new_height and GRASSVALUENOISE.seed == get_random_seed():
        return GRASSVALUENOISE
    else:  # Recreate with new width and height
        GRASSVALUENOISE = GrassValueNoise(new_width, new_height, get_random_seed())
        return GRASSVALUENOISE

def get_generic_noise_map(width, height):
    factory = ValueNoise
    pixel_width = math.ceil(width / factory.pixels_per_lattice) * factory.pixels_per_lattice
    pixel_height = math.ceil(height / factory.pixels_per_lattice) * factory.pixels_per_lattice
    noise = ValueNoise(pixel_width, pixel_height, 0)
    return noise

if __name__ == '__main__':
    noise = get_grass_noise_map(20, 20)
    total = 0
    for y in range(20):
        for x in range(20):
            val = noise.get(x, y)
            if val == 1 or val == 0:
                print("Wow!")
            total += val
            print("%.2f " % val, end='')
        print("")
    print(total / (20 * 20))
