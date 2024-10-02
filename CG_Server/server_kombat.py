import os
import time
import socket
import cv2
import qrcode
import gi
import numpy as np
import pandas as pd


gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Initialize GStreamer
Gst.init(None)

import hashlib

def hash_string(input_string, output_size):
    """Hashes a string using SHAKE and returns the hex digest with the given output size in bytes."""
    # Use SHAKE-128 for flexibility in output size
    shake = hashlib.shake_128()
    shake.update(input_string.encode('utf-8'))
    # Return the hex digest with the specified byte size
    return shake.hexdigest(output_size)

# Parameters
folder_path = "/home/alireza/cgserver/captured_Kombat"  # Folder containing PNG frames
fps = 30  # Frames per second
bitrate = 5000  # in kbps
resolution = (1364, 768)  # (width, height)(1920,1080)
player_ip = "200.18.102.9"  # IP address for streaming
player_port = 5000  # UDP port for streaming
# _______________________________________________________________________ This computer (CG Server Configuration) ________________________________________
cg_server_port = 5501  # Port for receiving control data from a socket
cg_server_ipadress = "0.0.0.0"   # this computer IP address

auto_commands_file_addr= 'autocommands_kombat.txt'



# Custom function to load autocommands.txt while handling the complex 'command' field
def load_autocommands(file_path):
    autocommands = []
    with open(file_path, 'r') as file:
        next(file)  # Skip the header line
        for line in file:
            # Split only on the last comma to avoid splitting inside the 'command' field
            parts = line.rsplit(',', 1)
            if len(parts) == 2:
                id_and_command, encrypted_cmd = parts
                # Split the ID from the command part
                id_str, command_str = id_and_command.split(',', 1)
                autocommands.append((int(id_str), command_str, encrypted_cmd.strip()))
    return pd.DataFrame(autocommands, columns=['ID', 'command', 'encrypted_cmd'])

# Load autocommand.txt
autocommands_df = load_autocommands(auto_commands_file_addr)

# List of frame IDs where we want to pause and wait for socket input
#pause_frame_ids = [100,500, 1000, 1200]  # Example: Pause on frame 5, 10, and 20

pause_frame_ids = [10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50, 54, 58, 62, 66, 71, 75, 79, 83, 87, 91, 95, 99, 103, 108, 111, 115, 119, 123, 127, 131, 136, 140, 144, 148, 152, 156, 160, 164, 168, 172, 176, 181, 185, 189, 193, 197, 201, 205, 209, 213, 217, 221, 225, 229, 234, 238, 241, 245, 249, 253, 257, 261, 265, 269, 273, 277, 281, 285, 289, 293, 297, 301, 305, 309, 313, 317, 321, 325, 329, 334, 338, 342, 346, 350, 354, 358, 363, 367, 371, 375, 379, 383, 387, 391, 395, 400, 404, 408, 412, 416, 420, 424, 428, 432, 436, 441, 444, 448, 453, 457, 460, 464, 468, 472, 476, 480, 484, 488, 492, 496, 500, 504, 508, 512, 517, 521, 525, 529, 533, 537, 541, 546, 550, 553, 557, 562, 566, 570, 574, 579, 582, 586, 590, 594, 598, 602, 607, 610, 615, 619, 623, 627, 631, 635, 639, 643, 647, 651, 655, 659, 663, 667, 671, 676, 679, 684, 688, 691, 695, 699, 703, 707, 711, 715, 720, 724, 727, 731, 735, 739, 743, 747, 751, 755, 759, 763, 767, 771, 775, 779, 784, 787, 791, 796, 799, 804, 808, 812, 816, 820, 824, 828, 832, 836, 840, 844, 848, 852, 856, 861, 865, 868, 873, 876, 880, 884, 888, 892, 896, 900, 904, 908, 913, 917, 921, 925, 929, 933, 937, 941, 945, 949, 953, 958, 962, 966, 970, 973, 977, 981, 985, 989, 993, 997, 1001, 1005, 1009, 1013, 1017, 1021, 1025, 1029, 1033, 1038, 1042, 1046, 1050, 1054, 1058, 1062, 1066, 1070, 1074, 1078, 1082, 1086, 1090, 1094, 1098, 1102, 1107, 1111, 1114, 1119, 1123, 1127, 1131, 1135, 1139, 1143, 1147, 1151, 1155, 1159, 1163, 1168, 1172, 1176, 1180, 1184, 1188, 1192, 1196, 1200, 1204, 1208, 1212, 1216, 1220, 1224, 1228, 1233, 1237, 1241, 1245, 1249, 1253, 1257, 1261, 1265, 1269, 1273, 1277, 1281, 1285, 1289, 1293, 1297, 1301, 1305, 1309, 1313, 1317, 1321, 1325, 1329, 1333, 1337, 1341, 1345, 1349, 1353, 1357, 1362, 1365, 1369, 1374, 1378, 1381, 1385, 1389, 1393, 1397, 1401, 1406, 1409, 1413, 1417, 1422, 1425, 1430, 1434, 1438, 1441, 1445, 1449, 1453, 1458, 1462, 1466, 1470, 1475, 1479, 1483, 1487, 1491, 1495, 1499, 1504, 1508, 1512, 1516, 1521, 1524, 1528, 1532, 1537, 1541, 1545, 1550, 1554, 1558, 1562, 1567, 1571, 1575, 1579, 1583, 1587, 1591, 1595, 1600, 1604, 1608, 1612, 1616, 1621, 1625, 1629, 1633, 1637, 1641, 1646, 1650, 1654, 1659, 1663, 1667, 1671, 1675, 1679, 1683, 1687, 1691, 1696, 1700, 1704, 1708, 1712, 1716, 1720, 1724, 1728, 1732, 1736, 1741, 1745, 1749, 1753, 1757, 1761, 1765, 1769, 1774, 1778, 1782, 1786, 1790, 1794, 1798, 1803, 1807, 1811, 1814, 1819, 1823, 1827, 1831, 1835, 1839, 1844, 1848, 1852, 1856, 1861, 1865, 1869, 1873, 1877, 1881, 1885, 1889, 1894, 1897, 1901, 1905, 1909, 1913, 1918, 1922, 1926, 1930, 1934, 1938, 1942, 1947, 1951, 1955, 1959, 1963, 1967, 1972, 1975, 1979, 1984, 1988, 1992, 1996, 2000, 2005, 2009, 2013, 2017, 2022, 2026, 2030, 2034, 2038, 2042, 2046, 2050, 2055, 2059, 2063, 2067, 2072, 2076, 2080, 2084, 2089, 2093, 2097, 2101, 2105, 2110, 2114, 2118, 2122, 2126, 2131, 2135, 2140, 2144, 2148, 2152, 2156, 2160, 2165, 2169, 2173, 2177, 2182, 2185, 2190, 2194, 2198, 2202, 2206, 2210, 2215, 2218, 2223, 2227, 2231, 2235, 2239, 2244, 2248, 2252, 2256, 2260, 2265, 2269, 2273, 2277, 2281, 2285, 2289, 2293, 2297, 2302, 2306, 2310, 2314, 2319, 2323, 2327, 2331, 2335, 2339, 2344, 2347, 2352, 2356, 2360, 2364, 2368, 2372, 2376, 2380, 2385, 2389, 2393, 2398, 2402, 2406, 2410, 2414, 2419, 2423, 2427, 2431, 2435, 2439, 2443, 2448, 2452, 2455, 2460, 2464, 2468, 2472, 2476, 2480, 2485, 2488, 2493, 2497, 2501, 2505, 2509, 2513, 2517, 2521, 2525, 2529, 2533, 2537, 2542, 2546, 2550, 2554, 2558, 2563, 2566, 2571, 2575, 2579, 2583, 2587, 2592, 2596, 2600, 2604, 2608, 2612, 2616, 2621, 2625, 2629, 2633, 2638, 2642, 2646, 2650, 2654, 2659, 2663, 2667, 2671, 2675, 2680, 2683, 2687, 2691, 2695, 2699, 2703, 2707, 2711, 2716, 2719, 2724, 2728, 2732, 2736, 2740, 2744, 2748, 2752, 2756, 2761, 2765, 2770, 2773, 2778, 2782, 2787, 2791, 2794, 2798, 2803, 2807, 2811, 2815, 2819, 2824, 2828, 2833, 2837, 2841, 2845, 2849, 2854, 2858, 2862, 2866, 2871, 2875, 2879, 2883, 2887, 2891, 2895, 2899, 2903, 2908, 2911, 2916, 2920, 2924, 2928, 2932, 2937, 2941, 2945, 2950, 2954, 2958, 2962, 2966, 2971, 2975, 2979, 2983, 2987, 2991, 2996, 3000, 3004, 3008, 3012, 3016, 3020, 3025, 3029, 3034, 3038, 3042, 3046, 3050, 3054, 3058, 3063, 3067, 3071, 3075, 3079, 3083, 3088, 3091, 3096, 3100, 3104, 3108, 3112, 3116, 3120, 3124, 3128, 3132, 3136, 3141, 3145, 3149, 3153, 3157, 3161, 3166, 3170, 3174, 3178, 3182, 3186, 3190, 3194, 3198, 3202, 3206, 3210, 3214, 3219, 3223, 3227, 3231, 3235, 3239, 3243, 3247, 3251, 3255, 3259, 3263, 3267, 3271, 3275, 3280, 3284, 3288, 3292, 3296, 3301, 3305, 3309, 3313, 3317, 3321, 3325, 3330, 3334, 3338, 3342, 3346, 3350, 3355, 3359, 3363, 3368, 3372, 3376, 3380, 3384, 3388, 3393, 3397, 3401, 3405, 3410, 3414, 3418, 3422, 3427, 3430, 3435, 3439, 3443, 3447, 3451, 3456, 3460, 3464, 3469, 3473, 3477, 3481, 3486, 3490, 3494, 3498, 3502, 3507, 3511, 3515, 3519, 3523, 3528, 3532, 3536, 3540, 3544, 3548, 3553, 3557, 3561, 3566, 3570, 3574, 3578, 3582, 3586, 3591, 3595, 3599, 3603, 3607, 3611, 3616, 3620, 3624, 3628, 3633, 3637, 3641, 3645, 3649, 3653, 3658, 3662, 3666, 3670, 3675, 3679, 3683, 3687, 3691, 3696, 3700, 3704, 3708, 3712, 3716, 3720, 3724, 3728, 3733, 3737, 3741, 3745, 3749, 3754, 3757, 3762, 3766, 3770, 3774, 3778, 3782, 3786, 3790, 3795, 3799, 3803, 3807, 3811, 3816, 3820, 3824, 3828, 3833, 3837, 3841, 3845, 3849, 3853, 3858, 3862, 3866, 3870, 3874, 3878, 3882, 3887, 3891, 3895, 3899, 3904, 3908, 3912, 3916, 3921, 3925, 3929, 3933, 3937, 3941, 3946, 3950, 3954, 3958, 3962, 3966, 3971, 3975, 3979, 3983, 3987, 3991, 3996, 4000, 4004, 4008, 4012, 4016, 4020, 4025, 4029, 4033, 4037, 4041, 4045, 4050, 4054, 4058, 4063, 4067, 4071, 4075, 4079, 4084, 4088, 4092, 4096, 4100, 4104, 4108, 4112, 4116, 4120, 4125, 4129, 4133, 4137, 4141, 4146, 4150, 4154, 4158, 4162, 4166, 4170, 4174, 4178, 4182, 4186, 4191, 4195, 4199, 4203, 4207, 4211, 4216, 4220, 4224, 4228, 4232, 4236, 4240, 4244, 4248, 4252, 4256, 4260, 4265, 4269, 4273, 4277, 4281, 4285, 4289, 4294, 4298, 4302, 4306, 4310, 4314, 4318, 4322, 4327, 4331, 4335, 4339, 4343, 4347, 4351, 4355, 4360, 4364, 4368, 4372, 4376, 4380, 4385, 4389, 4393, 4397, 4402, 4406, 4410, 4414, 4418, 4423, 4427, 4431, 4435, 4439, 4444, 4448, 4452, 4456, 4460, 4465, 4469, 4473, 4477, 4482, 4486, 4490, 4494, 4498, 4502, 4506, 4511, 4515, 4519, 4523, 4527, 4531, 4535, 4539, 4543, 4548, 4552, 4556, 4560, 4564, 4569, 4573, 4578, 4582, 4586, 4590, 4594, 4598, 4602, 4606, 4611, 4615, 4619, 4623, 4627, 4631, 4636, 4640, 4644, 4648, 4652, 4657, 4661, 4665, 4669, 4673, 4678, 4682, 4686, 4690, 4694, 4698, 4702, 4706, 4710, 4714, 4718, 4722, 4726, 4730, 4735, 4739, 4743, 4747, 4751, 4755, 4760, 4764, 4768, 4772, 4776, 4780, 4784, 4789, 4793, 4797, 4802, 4806, 4810, 4814, 4819, 4823, 4827, 4831, 4835, 4839, 4843, 4847, 4851, 4855, 4859, 4864, 4868, 4872, 4876, 4881, 4885, 4889, 4894, 4898, 4902, 4906, 4910, 4914, 4919, 4923, 4927, 4932, 4936, 4940, 4944, 4948, 4953, 4957, 4961, 4966, 4970, 4974, 4978, 4983, 4987, 4991, 4995, 4999, 5003, 5008, 5012, 5016, 5020, 5024, 5028, 5032, 5036, 5041, 5045, 5050, 5054, 5058, 5062, 5066, 5070, 5074, 5079, 5083, 5087, 5092, 5096, 5100, 5105, 5109, 5113, 5117, 5122, 5126, 5130, 5134, 5138, 5143, 5147, 5151, 5155, 5160, 5164, 5168, 5173, 5177, 5181, 5185, 5189, 5194, 5198, 5202, 5206, 5211, 5215, 5219, 5224, 5228, 5232, 5236, 5240, 5244, 5248, 5253, 5257, 5261, 5266, 5270, 5274, 5278, 5282, 5286, 5290, 5295, 5299, 5303, 5307, 5311, 5315, 5319, 5323, 5328, 5332, 5336, 5340, 5344, 5349, 5353, 5357, 5361, 5366, 5370, 5374, 5378, 5382, 5387, 5391, 5395, 5399, 5403, 5407, 5411, 5416, 5419, 5424, 5428, 5432, 5436, 5440, 5444, 5449, 5452, 5457, 5461, 5464, 5469, 5472, 5477, 5481, 5485, 5489, 5493, 5497, 5501, 5505, 5509, 5514, 5518, 5521, 5526, 5530, 5534, 5538, 5542, 5546, 5550, 5554, 5558, 5562, 5566, 5570, 5575, 5578, 5581, 5585, 5590, 5594, 5598, 5602, 5606, 5610, 5614, 5618, 5622, 5626, 5630, 5634, 5638, 5642, 5646, 5650, 5654, 5659, 5663, 5667, 5671, 5675, 5679, 5683, 5687, 5691, 5695, 5699, 5704, 5708, 5712, 5716, 5720, 5724, 5728, 5732, 5736, 5740, 5744, 5748, 5752, 5757, 5761, 5765, 5769, 5773, 5777, 5781, 5785, 5789, 5794, 5797, 5802, 5806, 5810, 5814, 5818, 5822, 5826, 5830, 5834, 5839, 5843, 5847, 5851, 5855, 5859, 5863, 5867, 5871, 5875, 5880, 5884, 5887, 5892, 5896, 5899, 5903, 5908, 5912, 5916, 5920, 5924, 5928, 5933, 5937, 5941, 5945, 5949, 5953, 5958, 5962, 5966, 5970, 5974, 5978, 5982, 5986, 5990, 5995, 5999, 6003, 6007, 6011, 6015, 6019, 6023, 6027, 6031, 6036, 6040, 6044, 6048, 6052, 6056, 6061, 6065, 6069, 6073, 6077, 6081, 6085, 6089, 6093, 6097, 6101, 6105, 6109, 6113, 6118, 6122, 6126, 6130, 6134, 6137, 6142, 6146, 6150, 6154, 6159, 6163, 6167, 6171, 6175, 6179, 6184, 6188, 6192, 6196, 6200, 6205, 6209, 6213, 6217, 6221, 6225, 6229, 6233, 6237, 6241, 6245, 6249, 6253, 6257, 6262, 6266, 6270, 6274, 6278, 6282, 6286, 6290, 6295, 6299, 6303, 6307, 6311, 6315, 6319, 6323, 6327, 6331, 6335, 6339, 6343, 6347, 6351, 6355, 6359, 6364, 6367, 6372, 6376, 6380, 6385, 6389, 6393, 6397, 6401, 6405, 6409, 6413, 6418, 6422, 6426, 6430, 6434, 6438, 6442, 6446, 6450, 6454, 6458, 6462, 6466, 6471, 6475, 6479, 6483, 6487, 6491, 6496, 6500, 6504, 6508, 6512, 6516, 6520, 6524, 6529, 6533, 6537, 6541, 6545, 6549, 6553, 6558, 6562, 6565, 6569, 6574, 6578, 6582, 6586, 6590, 6594, 6598, 6602, 6607, 6610, 6615, 6619, 6623, 6627, 6631, 6635, 6639, 6643, 6648, 6651, 6655, 6659, 6664, 6668, 6672, 6676, 6680, 6684, 6688, 6692, 6696, 6700, 6704, 6709, 6712, 6717, 6720, 6724, 6728, 6732, 6736, 6741, 6745, 6749, 6753, 6758, 6762, 6766, 6770, 6774, 6778, 6783, 6787, 6791, 6795, 6799, 6803, 6807, 6811, 6815, 6820, 6823, 6828, 6832, 6836, 6840, 6844, 6848, 6852, 6856, 6860, 6865, 6869, 6873, 6877, 6881, 6886, 6890, 6894, 6898, 6902, 6906, 6910, 6914, 6918, 6922, 6926, 6930, 6934, 6938, 6942, 6946, 6950, 6954, 6958, 6962, 6966, 6970, 6974, 6978, 6982, 6987, 6991, 6995, 6999, 7003, 7007, 7011, 7015, 7019, 7023, 7027, 7032, 7036, 7040, 7044, 7048, 7052, 7057, 7060, 7065, 7069, 7073, 7078, 7082, 7085, 7090, 7094, 7098, 7102, 7106, 7110, 7114, 7118, 7122, 7126, 7130, 7134, 7138, 7142, 7146, 7150, 7155, 7159, 7163, 7167, 7171, 7175, 7179, 7183, 7187, 7192, 7196, 7200, 7204, 7209, 7213, 7217, 7221, 7225, 7229, 7233, 7237, 7241, 7245, 7249, 7253, 7258, 7262, 7266, 7270, 7275, 7279, 7283, 7287, 7291, 7295, 7300, 7304, 7308, 7312, 7316, 7320, 7325, 7329, 7333, 7337, 7341, 7346, 7350, 7354, 7358, 7362, 7366, 7370, 7374, 7378, 7382, 7387, 7390, 7394, 7399, 7403, 7408, 7412, 7416, 7420, 7424, 7429, 7433, 7437, 7441, 7445, 7449, 7453, 7457, 7461, 7466, 7470, 7474, 7478, 7482, 7487, 7491, 7495, 7499, 7503, 7507, 7511, 7515, 7519, 7524, 7528, 7532, 7537, 7541, 7545, 7549, 7553, 7557, 7561, 7565, 7569, 7573, 7577, 7581, 7586, 7590, 7594, 7599, 7603, 7607, 7611, 7615, 7620, 7624, 7628, 7632, 7636, 7640, 7645, 7649, 7654, 7657, 7661, 7666, 7670, 7675, 7679, 7683, 7687, 7691, 7695, 7699, 7704, 7708, 7712, 7716, 7720, 7724, 7729, 7733, 7736, 7741, 7745, 7749, 7753, 7757, 7762, 7766, 7770, 7774, 7778, 7783, 7787, 7791, 7795, 7799, 7803, 7807, 7811, 7815, 7820, 7824, 7828, 7832, 7836, 7840, 7844, 7849, 7853, 7857, 7861, 7866, 7870, 7875, 7879, 7883, 7888, 7892, 7896, 7900, 7904, 7908, 7912, 7916, 7921, 7925, 7929, 7933, 7938, 7942, 7946, 7950, 7954, 7959, 7963, 7967, 7971, 7975, 7979, 7983, 7987, 7991, 7996, 8000, 8004, 8008, 8012, 8016, 8020, 8024, 8029, 8033, 8036, 8041, 8045, 8049, 8053, 8057, 8062, 8065, 8069, 8073, 8078, 8082, 8086, 8090, 8094, 8099, 8103, 8107, 8111, 8115, 8119, 8124, 8128, 8132, 8136, 8140, 8145, 8149, 8153, 8158, 8162, 8166, 8170, 8174, 8178, 8182, 8187, 8191, 8195, 8200, 8203, 8208, 8212, 8216, 8221, 8225, 8229, 8233, 8237, 8241, 8246, 8250, 8254, 8258, 8262, 8266, 8271, 8275, 8279, 8283, 8288, 8292, 8296, 8300, 8305, 8309, 8313, 8317, 8321, 8326, 8330, 8334, 8338, 8342, 8347, 8351, 8355, 8359, 8364, 8368, 8372, 8376, 8380, 8384, 8388, 8392, 8397, 8401, 8405, 8409, 8413, 8417, 8421, 8426, 8430, 8434, 8438, 8443, 8447, 8451, 8455, 8459, 8463, 8467, 8471, 8476, 8480, 8484, 8488, 8492, 8497, 8501, 8505, 8509, 8513, 8518, 8522, 8526, 8530, 8535, 8539, 8543, 8547, 8551, 8556, 8560, 8564, 8569, 8573, 8577, 8581, 8585, 8589, 8593, 8597, 8602, 8606, 8610, 8614, 8618, 8623, 8627, 8631, 8635, 8639, 8643, 8647, 8652, 8656, 8659, 8664, 8668, 8672, 8676, 8680, 8684, 8688, 8693, 8697, 8701, 8705, 8709, 8713, 8717, 8722, 8725, 8730, 8734, 8738, 8742, 8746, 8751, 8755, 8759, 8764, 8768, 8772, 8776, 8780, 8784, 8788, 8792, 8797, 8801, 8805, 8809, 8813, 8817, 8821, 8825, 8830, 8834, 8838, 8842, 8846, 8850, 8854, 8859, 8863, 8867, 8871, 8875, 8879, 8883, 8887, 8891, 8895, 8899, 8903, 8907, 8911, 8916, 8920, 8924]



def create_qr_code(frame_id, timestamp, resolution, bitrate, fps, mytry=1):
    """Create a QR code with frame information."""
    qr_data = f"ID:{frame_id}, Timestamp:{timestamp}, Resolution:{resolution}, Bitrate:{bitrate}kbps, FPS:{fps}, retry:{mytry}"
    qr = qrcode.QRCode(
        version=1,  # Smaller QR code
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=2,  # Adjust to make the QR code smaller
        border=2
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white')

    # Convert QR image to OpenCV format (BGR)
    qr_img = qr_img.convert('RGB')
    qr_cv = cv2.cvtColor(np.array(qr_img), cv2.COLOR_RGB2BGR)
    return qr_cv


def setup_socket():
    """Set up a UDP socket to send control messages."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Allow reuse of the same address and port
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    
    # Bind the socket to the specific source port (same as GStreamer)
    sock.bind((cg_server_ipadress, cg_server_port))  # socket_port should be 5501 or the same source port as GStreamer
    
    print(f"Listening on UDP port {cg_server_port} for control data...")
    return sock



def stream_frames():
    """Stream frames with QR code embedded over UDP using GStreamer."""
    # Set up the control socket
    control_socket = setup_socket()
    #source_port = 5501
    # GStreamer pipeline for video encoding and streaming
    pipeline_str = f"""
        appsrc name=source is-live=true block=true format=GST_FORMAT_TIME do-timestamp=true !
        videoconvert ! video/x-raw,format=I420,width={resolution[0]},height={resolution[1]},framerate={fps}/1 !
        x264enc bitrate={bitrate} speed-preset=ultrafast tune=zerolatency ! h264parse ! rtph264pay ! 
        udpsink host={player_ip} port={player_port} bind-port={cg_server_port}
    """
    
    # Parse and create the GStreamer pipeline
    pipeline = Gst.parse_launch(pipeline_str)

    # Get the 'appsrc' element from the pipeline
    appsrc = pipeline.get_by_name("source")
    if not appsrc:
        print("Failed to retrieve appsrc element from the pipeline.")
        return

    # Set the caps for the 'appsrc' element, including FPS and resolution
    appsrc.set_property("caps", Gst.Caps.from_string(f"video/x-raw,format=BGR,width={resolution[0]},height={resolution[1]},framerate={fps}/1"))

    # Start the pipeline
    pipeline.set_state(Gst.State.PLAYING)
    
    frame_id = 1  # Frame counter (starting from 1 for human-readable frame IDs)
    png_files = sorted([f for f in os.listdir(folder_path) if f.endswith(".png")])  # List PNG files

    for idx, file in enumerate(png_files):
        frame_path = os.path.join(folder_path, file)
        frame = cv2.imread(frame_path)  # Read the frame
        
        if frame is None:
            print(f"Could not load frame {file}")
            continue

        # Resize frame to the desired resolution
        frame = cv2.resize(frame, resolution)

        # Add QR code to the bottom-right corner of the frame
        timestamp = time.time() * 1000  # Timestamp in milliseconds
        qr_code_img = create_qr_code(frame_id, timestamp, resolution, bitrate, fps)
        qr_height, qr_width, _ = qr_code_img.shape

        # Ensure the QR code fits within the frame's dimensions
        x_offset = resolution[0] - qr_width - 8  # 10px from the right
        y_offset = resolution[1] - qr_height - 8  # 10px from the bottom

        # Ensure QR code does not go out of bounds
        if y_offset >= 0 and x_offset >= 0:
            frame[y_offset:y_offset + qr_height, x_offset:x_offset + qr_width] = qr_code_img

        # Convert frame to bytes and push to GStreamer
        gst_buffer = Gst.Buffer.new_wrapped(frame.tobytes())
        appsrc.emit("push-buffer", gst_buffer)

        # Log the frame that is being streamed
        print(f"Streaming frame {frame_id}")

        # To collectet the ineraction with Command sent/Received + Frame
        # if frame_id in pause_frame_ids:
            # with open("server_interaction.txt", "a") as f: f.write(f"{frame_id},{timestamp}\n")

        # Increment frame counter
        frame_id += 1

        if frame_id in pause_frame_ids:
            print(f"Frame ID {frame_id} is in the pause list. Waiting for control data...")

            try:
                # Find all matching commands for the current frame_id
                # matching_commands = None
                matching_commands = autocommands_df[autocommands_df['ID'] == frame_id]
                #print('Debug:', matching_commands.shape)

                # Iterate over each matching command
                for index, row in matching_commands.iterrows():
                    print(f"Waiting for control data for matching command {len(matching_commands)}")      #{index + 1} of {len(matching_commands)}")
                    
                    # Receive control data for each matching command (blocking)
                    data, addr = control_socket.recvfrom(1024)
                    received_data = data.decode().split(',')
                    # print(received_data)
                    received_time = time.time() * 1000  # Timestamp in nanosecond /old was milliseconds (*1000)


                    
                    
                    # Extract both timestamps and the command
                    send_time = received_data[0]
                    received_cmd = received_data[1]
                    #received_time = send_time
                    # dif = received_time - send_time
                    print(f"Received control data: Time = {send_time}, from {addr}") # Command = {received_cmd} from {addr}")

                    # Compare the received command with the current matching encrypted command
                    if row['encrypted_cmd'] == received_cmd:
                        print(f"ID={frame_id} & sent Time = {send_time} ms & received Time = {received_time} ms") # & command = {row['command']}")
                        with open("kombat_cmd_received.txt", "a") as f: f.write(f"{frame_id},{send_time},{received_time}\n")

                    else:
                        print('Oooops, no matching encrypted command found for this control data.')

            except socket.error as e:
                print(f"Socket error: {e}")

            




        # Maintain the frame rate
        time.sleep(1 / fps)

    # End the stream
    appsrc.emit("end-of-stream")
    pipeline.set_state(Gst.State.NULL)

if __name__ == "__main__":
    stream_frames()

    
