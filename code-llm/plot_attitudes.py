import matplotlib.pyplot as plt

def save_attitude_history(attitude_history, filename="attitude_history.png",N=100, k=10, p=0.1):
    time_steps = [entry[0] for entry in attitude_history]  # 提取时间步
    attitudes = list(zip(*[entry[1] for entry in attitude_history]))  # 按代理分组的态度值

    plt.figure(figsize=(10, 6))
    for i, attitude in enumerate(attitudes):
        plt.plot(time_steps, attitude)

    plt.xlabel('Time Step')
    plt.ylabel('Attitude')
    plt.title('Attitude Change Over Time')
    
    plt.text(0.95, 0.90, f'N = {N}, k = {k}, p = {p}', ha='right', va='top', transform=plt.gca().transAxes)

    plt.ylim(-1, 1)  # Y 轴范围为 [-1, 1]
    plt.grid(True)
    plt.savefig(filename)
    print(f"Saved plot to {filename}")









