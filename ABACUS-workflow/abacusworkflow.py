NUM = 4 #计算温度值的数量
import getpass
from dflow import config, s3_config
from dflow.plugins import bohrium
from dflow.plugins.bohrium import TiefblueClient
config["host"] = "https://workflows.deepmodeling.com"
config["k8s_api_server"] = "https://workflows.deepmodeling.com"
bohrium.config["username"] = "2000011003@stu.pku.edu.cn"
bohrium.config["password"] = "Kepler08051005@"
bohrium.config["project_id"] = 15069
s3_config["repo_key"] = "oss-bohrium"
s3_config["storage_client"] = TiefblueClient()
from dflow.plugins.dispatcher import DispatcherExecutor

dispatcher_executor = DispatcherExecutor(
        machine_dict={
            "batch_type": "Bohrium",
            "context_type": "Bohrium",
            "remote_profile": {
                "input_data": {
                    "job_type": "container",
                    "platform": "ali",
                    "scass_type" : "c32_m128_4 * NVIDIA V100"
                },
            },
        },
    )

from typing import List
from dflow import Step, Workflow
from dflow.python import OP, OPIO, Artifact, OPIOSign, PythonOPTemplate, Slices
from dflow.utils import upload_artifact, download_artifact
import os
from pathlib import Path
import subprocess
import shutil
import numpy as np


class DPMD(OP):
    def __init__(self):
        pass
         
    @classmethod
    def get_input_sign(cls):
        return OPIOSign({
            "ABACUS_INPUT": Artifact(Path), #一系列输入文件
            "md_tfirst_file":Artifact(Path), #温度文件路径
            "index": int
        })

    @classmethod
    def get_output_sign(cls):
        return OPIOSign({
            "ABACUS_output_folder": Artifact(Path),  #OUT.suffix的路径
            "diffusion_coefficient": Artifact(Path)  
        })

    @OP.exec_sign_check
    def execute(
            self,
            op_in: OPIO,
    ) -> OPIO:
        cwd = os.getcwd()
        '''
        # Get the directory path of the "md_tfirst_file"
        md_tfirst_file_dir = os.path.dirname(op_in["md_tfirst_file"])

        # Change the current working directory to the directory containing the "md_tfirst_file"
        os.chdir(md_tfirst_file_dir)
        '''
        md_tfirst_file_path = os.path.join(op_in["md_tfirst_file"])
        index = op_in["index"]
        # Read the new value from the "md_tfirst_file"
        with open(md_tfirst_file_path, "r") as f:
           line = f.readline().strip()  # Read the first line and strip whitespace characters
           values = line.split()  # Split the line into a list of values
           new_md_tfirst = values[index]  # Get the second value (index 1)
        
        os.chdir(op_in["ABACUS_INPUT"] )
        # 进入 ABACUS_INPUT 文件夹下的 INPUT 文件
        input_file_path = os.path.join(op_in["ABACUS_INPUT"], "INPUT")
    
        # 打开 INPUT 文件并读取内容
        with open(input_file_path, "r") as f:
         content = f.read()

       # 寻找 md_tfirst 参数所在的行
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if "md_tfirst" in line:
                # 拆分行为参数名和参数值
                parts = line.split()
                param_name = parts[0]
                old_value = parts[1]

                # 将参数值替换为新值
                new_value = new_md_tfirst  # 设置新的 md_tfirst 值
                parts[1] = new_value

                # 将修改后的行重新组合成字符串
                new_line = " ".join(parts)
                
                # 将新行替换回原始内容
                lines[i] = new_line
                break
    
        # 更新文件内容
        new_content = "\n".join(lines)
    
        # 保存修改后的文件内容
        with open(input_file_path, "w") as f:
             f.write(new_content)
    
        # 执行计算任务
        cmd =  "abacus" 
        subprocess.call(cmd, shell=True)
        os.chdir("./OUT.DPMD-melting")
        
        # 创建名为myCandela的新文件夹
        new_folder = "myCandela"
        if not os.path.exists(new_folder):
            os.mkdir(new_folder)

        # 复制MD_dump文件到myCandela文件夹中
        old_file = "MD_dump"
        new_path = os.path.join(new_folder, old_file)
        shutil.copy2(old_file, new_path)
        os.chdir(new_folder)
        # 执行计算任务
        cmd =  "tree" 
        subprocess.call(cmd, shell=True)

        #准备Candela输入文件
        content = '''
        calculation  msd # Pair Distribution Function.
        system ZnS
        geo_in_type  ABACUS
        geo_directory MD_dump
        geo_1        1
        geo_2        25000
        geo_interval 1
        geo_ignore   0

        ntype        2        # number of different types of atoms.
        natom        216   # total number of atoms.
        natom1       108   #Zn
        natom2       108   #S
        id1          Zn
        id2          S
        msd_dt       0.002
        '''
        with open("INPUT", "w") as file:
            file.write(content)

        # 执行计算任务
        cmd =  "candela" 
        subprocess.call(cmd, shell=True)

        # 读取MSD.dat文件
        data = np.loadtxt('MSD.dat')

        # 提取时间和平均方位移数据
        time = data[:, 0]
        msd = data[:, 2]

        # 计算扩散系数
        slope, intercept = np.polyfit(time, msd, 1)
        diffusion_coefficient = slope / 2

        # 将扩散系数写入文件
        filename = str(new_md_tfirst)+"K_result.txt"
        file_path = Path(filename)
        with file_path.open("w") as file:
            file.write(str(diffusion_coefficient))
        print("温度：", new_md_tfirst,"K")
        print("扩散系数：", diffusion_coefficient)
        return OPIO({
            "ABACUS_output_folder":Path(op_in["ABACUS_INPUT"])/"OUT.DPMD-melting",
            "diffusion_coefficient":file_path
        })       



from dflow import Workflow
wf = Workflow(name = "my-abacus-dpmd-workflow")
DPMD = Step(name = "DPMD",
            template = PythonOPTemplate(DPMD,image ="registry.dp.tech/dptech/prod-12058/abacus-deepmd-kit-candela:abacus-deepmd-kit-candela_v1.01",
            slices=Slices("{{item}}",
                    input_parameter=["index"],
                    output_artifact=["ABACUS_output_folder","diffusion_coefficient"]
                )),
            parameters={"index": [x for x in range(NUM)]},
            with_param=range(NUM),
            artifacts={ "ABACUS_INPUT": upload_artifact("DPMD"),
                        "md_tfirst_file":upload_artifact("md_tfirst_file")},
            executor = dispatcher_executor)
wf.add(DPMD)
wf.submit()

'''
# 监控任务进程并下载文件
import time
while wf.query_status() in ["Pending", "Running"]:
    time.sleep(4)
assert(wf.query_status() == 'Succeeded')
NUM = 3
for i in range(NUM):
    step= wf.query_step(name="DPMD")[i]
    download_artifact(step[i].outputs.artifacts["output"])  
'''
