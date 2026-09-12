#!/usr/bin/env -S uv run --script --no-project
# /// script
# dependencies = ["numpy", "plotly"]
# ///

import numpy as np
import math
import time
import plotly.graph_objects as plotly

MESSAGE_FILE = "message.txt"
OUT = "message.html"

RULESET_INVALID = [-1] * 256
BLOCKSTATES = [
    ((0,0,0,0),(0,0,0,0)),((1,0,0,0),(0,0,0,0)),((0,1,0,0),(0,0,0,0)),((1,1,0,0),(0,0,0,0)),((0,0,1,0),(0,0,0,0)),((1,0,1,0),(0,0,0,0)),((0,1,1,0),(0,0,0,0)),((1,1,1,0),(0,0,0,0)),((0,0,0,1),(0,0,0,0)),((1,0,0,1),(0,0,0,0)),((0,1,0,1),(0,0,0,0)),((1,1,0,1),(0,0,0,0)),((0,0,1,1),(0,0,0,0)),((1,0,1,1),(0,0,0,0)),((0,1,1,1),(0,0,0,0)),((1,1,1,1),(0,0,0,0)),
    ((0,0,0,0),(1,0,0,0)),((1,0,0,0),(1,0,0,0)),((0,1,0,0),(1,0,0,0)),((1,1,0,0),(1,0,0,0)),((0,0,1,0),(1,0,0,0)),((1,0,1,0),(1,0,0,0)),((0,1,1,0),(1,0,0,0)),((1,1,1,0),(1,0,0,0)),((0,0,0,1),(1,0,0,0)),((1,0,0,1),(1,0,0,0)),((0,1,0,1),(1,0,0,0)),((1,1,0,1),(1,0,0,0)),((0,0,1,1),(1,0,0,0)),((1,0,1,1),(1,0,0,0)),((0,1,1,1),(1,0,0,0)),((1,1,1,1),(1,0,0,0)),
    ((0,0,0,0),(0,1,0,0)),((1,0,0,0),(0,1,0,0)),((0,1,0,0),(0,1,0,0)),((1,1,0,0),(0,1,0,0)),((0,0,1,0),(0,1,0,0)),((1,0,1,0),(0,1,0,0)),((0,1,1,0),(0,1,0,0)),((1,1,1,0),(0,1,0,0)),((0,0,0,1),(0,1,0,0)),((1,0,0,1),(0,1,0,0)),((0,1,0,1),(0,1,0,0)),((1,1,0,1),(0,1,0,0)),((0,0,1,1),(0,1,0,0)),((1,0,1,1),(0,1,0,0)),((0,1,1,1),(0,1,0,0)),((1,1,1,1),(0,1,0,0)),
    ((0,0,0,0),(1,1,0,0)),((1,0,0,0),(1,1,0,0)),((0,1,0,0),(1,1,0,0)),((1,1,0,0),(1,1,0,0)),((0,0,1,0),(1,1,0,0)),((1,0,1,0),(1,1,0,0)),((0,1,1,0),(1,1,0,0)),((1,1,1,0),(1,1,0,0)),((0,0,0,1),(1,1,0,0)),((1,0,0,1),(1,1,0,0)),((0,1,0,1),(1,1,0,0)),((1,1,0,1),(1,1,0,0)),((0,0,1,1),(1,1,0,0)),((1,0,1,1),(1,1,0,0)),((0,1,1,1),(1,1,0,0)),((1,1,1,1),(1,1,0,0)),
    ((0,0,0,0),(0,0,1,0)),((1,0,0,0),(0,0,1,0)),((0,1,0,0),(0,0,1,0)),((1,1,0,0),(0,0,1,0)),((0,0,1,0),(0,0,1,0)),((1,0,1,0),(0,0,1,0)),((0,1,1,0),(0,0,1,0)),((1,1,1,0),(0,0,1,0)),((0,0,0,1),(0,0,1,0)),((1,0,0,1),(0,0,1,0)),((0,1,0,1),(0,0,1,0)),((1,1,0,1),(0,0,1,0)),((0,0,1,1),(0,0,1,0)),((1,0,1,1),(0,0,1,0)),((0,1,1,1),(0,0,1,0)),((1,1,1,1),(0,0,1,0)),
    ((0,0,0,0),(1,0,1,0)),((1,0,0,0),(1,0,1,0)),((0,1,0,0),(1,0,1,0)),((1,1,0,0),(1,0,1,0)),((0,0,1,0),(1,0,1,0)),((1,0,1,0),(1,0,1,0)),((0,1,1,0),(1,0,1,0)),((1,1,1,0),(1,0,1,0)),((0,0,0,1),(1,0,1,0)),((1,0,0,1),(1,0,1,0)),((0,1,0,1),(1,0,1,0)),((1,1,0,1),(1,0,1,0)),((0,0,1,1),(1,0,1,0)),((1,0,1,1),(1,0,1,0)),((0,1,1,1),(1,0,1,0)),((1,1,1,1),(1,0,1,0)),
    ((0,0,0,0),(0,1,1,0)),((1,0,0,0),(0,1,1,0)),((0,1,0,0),(0,1,1,0)),((1,1,0,0),(0,1,1,0)),((0,0,1,0),(0,1,1,0)),((1,0,1,0),(0,1,1,0)),((0,1,1,0),(0,1,1,0)),((1,1,1,0),(0,1,1,0)),((0,0,0,1),(0,1,1,0)),((1,0,0,1),(0,1,1,0)),((0,1,0,1),(0,1,1,0)),((1,1,0,1),(0,1,1,0)),((0,0,1,1),(0,1,1,0)),((1,0,1,1),(0,1,1,0)),((0,1,1,1),(0,1,1,0)),((1,1,1,1),(0,1,1,0)),
    ((0,0,0,0),(1,1,1,0)),((1,0,0,0),(1,1,1,0)),((0,1,0,0),(1,1,1,0)),((1,1,0,0),(1,1,1,0)),((0,0,1,0),(1,1,1,0)),((1,0,1,0),(1,1,1,0)),((0,1,1,0),(1,1,1,0)),((1,1,1,0),(1,1,1,0)),((0,0,0,1),(1,1,1,0)),((1,0,0,1),(1,1,1,0)),((0,1,0,1),(1,1,1,0)),((1,1,0,1),(1,1,1,0)),((0,0,1,1),(1,1,1,0)),((1,0,1,1),(1,1,1,0)),((0,1,1,1),(1,1,1,0)),((1,1,1,1),(1,1,1,0)),
    ((0,0,0,0),(0,0,0,1)),((1,0,0,0),(0,0,0,1)),((0,1,0,0),(0,0,0,1)),((1,1,0,0),(0,0,0,1)),((0,0,1,0),(0,0,0,1)),((1,0,1,0),(0,0,0,1)),((0,1,1,0),(0,0,0,1)),((1,1,1,0),(0,0,0,1)),((0,0,0,1),(0,0,0,1)),((1,0,0,1),(0,0,0,1)),((0,1,0,1),(0,0,0,1)),((1,1,0,1),(0,0,0,1)),((0,0,1,1),(0,0,0,1)),((1,0,1,1),(0,0,0,1)),((0,1,1,1),(0,0,0,1)),((1,1,1,1),(0,0,0,1)),
    ((0,0,0,0),(1,0,0,1)),((1,0,0,0),(1,0,0,1)),((0,1,0,0),(1,0,0,1)),((1,1,0,0),(1,0,0,1)),((0,0,1,0),(1,0,0,1)),((1,0,1,0),(1,0,0,1)),((0,1,1,0),(1,0,0,1)),((1,1,1,0),(1,0,0,1)),((0,0,0,1),(1,0,0,1)),((1,0,0,1),(1,0,0,1)),((0,1,0,1),(1,0,0,1)),((1,1,0,1),(1,0,0,1)),((0,0,1,1),(1,0,0,1)),((1,0,1,1),(1,0,0,1)),((0,1,1,1),(1,0,0,1)),((1,1,1,1),(1,0,0,1)),
    ((0,0,0,0),(0,1,0,1)),((1,0,0,0),(0,1,0,1)),((0,1,0,0),(0,1,0,1)),((1,1,0,0),(0,1,0,1)),((0,0,1,0),(0,1,0,1)),((1,0,1,0),(0,1,0,1)),((0,1,1,0),(0,1,0,1)),((1,1,1,0),(0,1,0,1)),((0,0,0,1),(0,1,0,1)),((1,0,0,1),(0,1,0,1)),((0,1,0,1),(0,1,0,1)),((1,1,0,1),(0,1,0,1)),((0,0,1,1),(0,1,0,1)),((1,0,1,1),(0,1,0,1)),((0,1,1,1),(0,1,0,1)),((1,1,1,1),(0,1,0,1)),
    ((0,0,0,0),(1,1,0,1)),((1,0,0,0),(1,1,0,1)),((0,1,0,0),(1,1,0,1)),((1,1,0,0),(1,1,0,1)),((0,0,1,0),(1,1,0,1)),((1,0,1,0),(1,1,0,1)),((0,1,1,0),(1,1,0,1)),((1,1,1,0),(1,1,0,1)),((0,0,0,1),(1,1,0,1)),((1,0,0,1),(1,1,0,1)),((0,1,0,1),(1,1,0,1)),((1,1,0,1),(1,1,0,1)),((0,0,1,1),(1,1,0,1)),((1,0,1,1),(1,1,0,1)),((0,1,1,1),(1,1,0,1)),((1,1,1,1),(1,1,0,1)),
    ((0,0,0,0),(0,0,1,1)),((1,0,0,0),(0,0,1,1)),((0,1,0,0),(0,0,1,1)),((1,1,0,0),(0,0,1,1)),((0,0,1,0),(0,0,1,1)),((1,0,1,0),(0,0,1,1)),((0,1,1,0),(0,0,1,1)),((1,1,1,0),(0,0,1,1)),((0,0,0,1),(0,0,1,1)),((1,0,0,1),(0,0,1,1)),((0,1,0,1),(0,0,1,1)),((1,1,0,1),(0,0,1,1)),((0,0,1,1),(0,0,1,1)),((1,0,1,1),(0,0,1,1)),((0,1,1,1),(0,0,1,1)),((1,1,1,1),(0,0,1,1)),
    ((0,0,0,0),(1,0,1,1)),((1,0,0,0),(1,0,1,1)),((0,1,0,0),(1,0,1,1)),((1,1,0,0),(1,0,1,1)),((0,0,1,0),(1,0,1,1)),((1,0,1,0),(1,0,1,1)),((0,1,1,0),(1,0,1,1)),((1,1,1,0),(1,0,1,1)),((0,0,0,1),(1,0,1,1)),((1,0,0,1),(1,0,1,1)),((0,1,0,1),(1,0,1,1)),((1,1,0,1),(1,0,1,1)),((0,0,1,1),(1,0,1,1)),((1,0,1,1),(1,0,1,1)),((0,1,1,1),(1,0,1,1)),((1,1,1,1),(1,0,1,1)),
    ((0,0,0,0),(0,1,1,1)),((1,0,0,0),(0,1,1,1)),((0,1,0,0),(0,1,1,1)),((1,1,0,0),(0,1,1,1)),((0,0,1,0),(0,1,1,1)),((1,0,1,0),(0,1,1,1)),((0,1,1,0),(0,1,1,1)),((1,1,1,0),(0,1,1,1)),((0,0,0,1),(0,1,1,1)),((1,0,0,1),(0,1,1,1)),((0,1,0,1),(0,1,1,1)),((1,1,0,1),(0,1,1,1)),((0,0,1,1),(0,1,1,1)),((1,0,1,1),(0,1,1,1)),((0,1,1,1),(0,1,1,1)),((1,1,1,1),(0,1,1,1)),
    ((0,0,0,0),(1,1,1,1)),((1,0,0,0),(1,1,1,1)),((0,1,0,0),(1,1,1,1)),((1,1,0,0),(1,1,1,1)),((0,0,1,0),(1,1,1,1)),((1,0,1,0),(1,1,1,1)),((0,1,1,0),(1,1,1,1)),((1,1,1,0),(1,1,1,1)),((0,0,0,1),(1,1,1,1)),((1,0,0,1),(1,1,1,1)),((0,1,0,1),(1,1,1,1)),((1,1,0,1),(1,1,1,1)),((0,0,1,1),(1,1,1,1)),((1,0,1,1),(1,1,1,1)),((0,1,1,1),(1,1,1,1)),((1,1,1,1),(1,1,1,1))
]

# ============================================================

def generateHist(ruleset, historySize, mapSize, seed=None):
    if seed == None:
        seed = int(time.time())
        print(f"gen seed: {seed}")

    map = initArr((mapSize, mapSize, mapSize), seed)
    hist = initArr((historySize, mapSize, mapSize, mapSize), seed)

    steps = 1
    while steps <= historySize:
        hist[steps-1:steps] = map
        step_forwards(map, ruleset, steps)
        steps += 1

    return hist

def initArr(shape, seed):
    return np.random.default_rng(seed).integers(0, 2, size=shape)

def step_forwards(map, rules, step):
    zSize, ySize, xSize = map.shape

    for z in range(zSize >> 1):
        for y in range(ySize >> 1):
            for x in range(xSize >> 1):
                blockState = calcBlockState(map, x*2 + (step&1), y*2 + ((step&2)!=0), z*2 + ((step&4)!=0))
                nextBlockState = rules[blockState]
                setBlockState(map, x*2 + (step&1), y*2 + ((step&2)!=0), z*2 + ((step&4)!=0), nextBlockState)

def calcBlockState(map, x, y, z):
    zSize, ySize, xSize = map.shape

    return map[ z   %zSize][ y   %ySize][ x   %xSize]     + \
           map[ z   %zSize][ y   %ySize][(x+1)%xSize] * 2 + \
           map[ z   %zSize][(y+1)%ySize][ x   %xSize] * 4 + \
           map[ z   %zSize][(y+1)%ySize][(x+1)%xSize] * 8 + \
           map[(z+1)%zSize][ y   %ySize][ x   %xSize] * 16 + \
           map[(z+1)%zSize][ y   %ySize][(x+1)%xSize] * 32 + \
           map[(z+1)%zSize][(y+1)%ySize][ x   %xSize] * 64 + \
           map[(z+1)%zSize][(y+1)%ySize][(x+1)%xSize] * 128

def setBlockState(map, x, y, z, state):
    global BLOCKSTATES
    (a,b,c,d),(e,f,g,h) = BLOCKSTATES[state]
    zSize, ySize, xSize = map.shape

    map[ z   %zSize][ y   %ySize][ x   %xSize] = a
    map[ z   %zSize][ y   %ySize][(x+1)%xSize] = b
    map[ z   %zSize][(y+1)%ySize][ x   %xSize] = c
    map[ z   %zSize][(y+1)%ySize][(x+1)%xSize] = d
    map[(z+1)%zSize][ y   %ySize][ x   %xSize] = e
    map[(z+1)%zSize][ y   %ySize][(x+1)%xSize] = f
    map[(z+1)%zSize][(y+1)%ySize][ x   %xSize] = g
    map[(z+1)%zSize][(y+1)%ySize][(x+1)%xSize] = h

# ============================================================

def encode_msg_to_ruleset(msg):
    msg_bytes = msg.encode('utf-8')
    msg_num = int.from_bytes(msg_bytes, 'big')

    if msg_num >= math.factorial(256):
        print("Flag too long (~210)")
        exit(1)

    factoradic = []

    for i in range(256):
        msg_num, rem = divmod(msg_num, i+1)
        factoradic.append(rem)

    factoradic.reverse()

    l = list(range(256))
    ruleset = []

    for skip_count in factoradic:
        selected_number = l.pop(skip_count)
        ruleset.append(selected_number)

    return ruleset

# ============================================================

def build_voxel_mesh(data_array):
    z, y, x = np.where(data_array == 1)

    if len(x) == 0:
        return np.zeros((0, 3), dtype=np.int8)

    cube_vertices = np.array([
        [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], 
        [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]  
    ], dtype=np.int8)

    offsets = np.stack([x, y, z], axis=1)
    vertices = (offsets[:, np.newaxis, :] + cube_vertices[np.newaxis, :, :]).reshape(-1, 3)

    return vertices

def pad_vertices(v_array, max_voxels):
    padded = np.full((max_voxels * 8, 3), 0, dtype=np.int8)
    if len(v_array) > 0:
        padded[:len(v_array)] = v_array
    return padded

def gen_plotly(grid_size, arrays_sequence):
    try:
        max_voxels = max(np.sum(arr == 1) for arr in arrays_sequence)

        base_i = np.array([0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3])
        base_j = np.array([1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 0, 4])
        base_k = np.array([2, 3, 6, 7, 5, 4, 6, 5, 7, 6, 4, 7])

        v_offsets = np.arange(max_voxels) * 8
        i_faces = (base_i[np.newaxis, :] + v_offsets[:, np.newaxis]).flatten().tolist()
        j_faces = (base_j[np.newaxis, :] + v_offsets[:, np.newaxis]).flatten().tolist()
        k_faces = (base_k[np.newaxis, :] + v_offsets[:, np.newaxis]).flatten().tolist()
        v_initial = pad_vertices(build_voxel_mesh(arrays_sequence[0]), max_voxels)

        fig = plotly.Figure(
            data=[
                plotly.Mesh3d(
                    x=v_initial[:, 0].tolist(),
                    y=v_initial[:, 1].tolist(),
                    z=v_initial[:, 2].tolist(),
                    i=i_faces, 
                    j=j_faces, 
                    k=k_faces,
                    color="#914EE9", 
                    flatshading=True,
                    lighting=dict(ambient=0.6, diffuse=0.8, roughness=0.1),
                )
            ]
        )

        plotly_frames = []
        for idx, array_data in enumerate(arrays_sequence):
            v = pad_vertices(build_voxel_mesh(array_data), max_voxels)
            frame = plotly.Frame(
                data=[
                    plotly.Mesh3d(
                        x=v[:, 0].tolist(),
                        y=v[:, 1].tolist(),
                        z=v[:, 2].tolist()
                    )
                ],
                name=str(idx)
            )
            plotly_frames.append(frame)

        fig.frames = plotly_frames

        fig.update_layout(
            title="message",
            scene=dict(
                xaxis=dict(title='X', range=[0, grid_size]),
                yaxis=dict(title='Y', range=[0, grid_size]),
                zaxis=dict(title='Z', range=[0, grid_size]),
                aspectmode='cube' 
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            autosize=True,
            updatemenus=[dict(
                type="buttons",
                buttons=[
                    dict(
                        label="Pause", method="animate",
                        args=[
                            None, dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))
                        ]
                    ),
                    dict(
                        label="Play", method="animate",
                        args=[
                            None, dict(frame=dict(duration=300, redraw=True), mode="immediate", transition=dict(duration=0), fromcurrent=True)
                        ]
                    ),
                ]
            )]
        )

        fig.write_html(OUT, auto_play=False, include_plotlyjs="cdn", full_html=False, config={"responsive": True})

    except Exception as e:
        print("could not display")
        print(e)

# ============================================================

message = open(MESSAGE_FILE, 'r').read()
print(f"message = {message}")

ruleset = encode_msg_to_ruleset(message)
print(f"generated ruleset: {ruleset}")

history_size = 128
map_size = 4
seed = None

hist = generateHist(ruleset, history_size, map_size, seed)

# Make sure your message is reversible before sending.

gen_plotly(map_size, hist)
