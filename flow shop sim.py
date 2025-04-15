# 1. 3대의 기계, 5개의 작업
# 2. job_generator가 5개의 작업을 5 시간 간격으로 생성
# 3. 모든 작업들은 순차적으로 진행되어, 각각의 시작 시간, 종료 시간, 그리고 각 단계에서의 처리 시간 기록
# 4. 각 기계는 한 번에 한 작업만 처리할 수 있으므로, 작업이 기계에 접근하면 먼저 사용 중인 작업이 있는지 확인
# 5. 모든 작업이 처리된 후, 각 작업의 시작 시각, 종료 시각, 총 사이클 타임 및 각 기계에서 기다린 시간이 최종적으로 출력

import simpy


# Machine 클래스: 각 기계(리소스)

class Machine:
    """
    정의
    Machine 클래스는 Flow Shop 환경에서 각 작업이 처리되는 기계
    
    Attributes:
      env: simpy.Environment 객체
      name: 기계의 이름(식별자)
      resource: simpy.Resource 객체로, 한 번에 하나의 작업만 처리하도록 capacity=1 설정
    """
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.resource = simpy.Resource(env, capacity=1)


# Job: 처리할 작업(작업 단위)

class Job:
    """
    정의
    Job 클래스는 각 작업의 상세 정보를 포함합니다.
    
    Attributes:
      id:
      processing_times: 각 기계에서의 처리 시간 리스트
      start_time: 시작한 시간
      end_time: 완료 시간
      waiting_times: 각 기계에서 대기한 시간들을 저장하는 리스트
    """
    def __init__(self, id, processing_times):
        self.id = id
        self.processing_times = processing_times
        self.start_time = None
        self.end_time = None
        self.waiting_times = []  # 각 기계에서의 대기한 시간 저장


# process_job 함수: 하나의 작업이 모든 기계를 순차적으로 처리하는 과정을 시뮬레이션

def process_job(env, job, machines, statistics):
    """
    정의
    하나의 Job이 Flow Shop의 모든 기계를 순차 처리하는 과정을 정의
    
    Args:
      env: simpy
      job:
      machines: 처리 순서대로 배치된 Machine
      statistics: 작업 완료 통계 데이터를 저장할 dict
    """
    # 작업 시작 시각 기록
    print(f"[Time {env.now}] Job {job.id} 시작")
    job.start_time = env.now

    # 각 기계를 순차적으로 접근
    for i, machine in enumerate(machines):
        # 기계 자원 요청(한 번에 하나만)
        with machine.resource.request() as request:
            wait_start = env.now  # 대기 시작 시각 기록
            yield request       # 기계 사용이 가능할 때까지 대기
            wait_time = env.now - wait_start  # 대기 시간 계산
            job.waiting_times.append(wait_time)
            print(f"[Time {env.now}] Job {job.id}가 {machine.name} 사용 시작 (대기 시간: {wait_time})")
            
            # 지정된 처리 시간만큼 작업 수행
            process_time = job.processing_times[i]
            yield env.timeout(process_time)
            print(f"[Time {env.now}] Job {job.id}가 {machine.name} 처리 완료 (처리 시간: {process_time})")
    
    # 모든 기계 처리 후 작업 종료 기록
    job.end_time = env.now
    total_cycle_time = job.end_time - job.start_time
    statistics['jobs'].append(job)
    statistics['cycle_times'].append(total_cycle_time)
    print(f"[Time {env.now}] Job {job.id} 완료 (총 사이클 타임: {total_cycle_time})")


# job_generator 함수: 작업 데이터를 기반으로 순차적으로 Job 프로세스를 생성

def job_generator(env, machines, statistics, arrival_interval, jobs_data):
    """
    정의
    각 작업 데이터를 받아 Job을 생성, 시뮬레이션에 등록
    
    Args:
      env: simpy
      machines:
      statistics: 시뮬레이션 통계 데이터를 저장할 dict
      arrival_interval: 작업 간의 도착 간격
      jobs_data: 작업 데이터 리스트. 각 요소는 (job_id, [각 기계의 처리시간]) 튜플
    """
    for job_info in jobs_data:
        job_id, processing_times = job_info
        job = Job(job_id, processing_times)
        env.process(process_job(env, job, machines, statistics))
        # 다음 작업 생성 전 지정한 arrival_interval만큼 대기
        yield env.timeout(arrival_interval)


# run_simulation 함수: 전체 시뮬레이션 환경 구성, 실행 및 통계 수집

def run_simulation(sim_time, num_machines, jobs_data, arrival_interval):
    """
    정의
    Flow Shop 시뮬레이션을 실행하는 메인 함수
    
    Args:
      sim_time: 전체 시뮬레이션 실행 시간
      num_machines: Flow Shop에서 사용될 기계의 수
      jobs_data: 각 작업의 데이터 리스트 [(job_id, [기계별 처리시간]), ...]
      arrival_interval: 작업 간의 도착 간격
    
    Returns:
      statistics: 시뮬레이션 수행 후의 통계 데이터를 담은 dict
    """
    statistics = {
        'jobs': [],         # 완료된 Job 객체 리스트
        'cycle_times': []   # 각 Job의 총 사이클 타임
    }
    # simpy 환경 생성
    env = simpy.Environment()
    # 지정 수의 기계 객체 생성 (예: Machine_1, Machine_2, ...)
    machines = [Machine(env, f"Machine_{i+1}") for i in range(num_machines)]
    # 작업 생성자 프로세스 등록
    env.process(job_generator(env, machines, statistics, arrival_interval, jobs_data))
    # 설정한 전체 시간만큼 시뮬레이션 실행
    env.run(until=sim_time)
    return statistics


# 메인 실행 영역: 시뮬레이션 파라미터 설정, 실행 및 결과 출력

if __name__ == '__main__':
    # 시뮬레이션 파라미터 설정
    sim_time = 100            # 전체 시뮬레이션 실행 시간 (예: 100 시간)
    num_machines = 3          # Flow Shop에 사용될 기계 수
    arrival_interval = 5      # 작업들 간의 도착 간격
    
    # 작업 데이터 설정
    # 각 작업은 (job_id, [Machine_1 처리시간, Machine_2 처리시간, Machine_3 처리시간])
    jobs_data = [
        (1, [3, 2, 4]),
        (2, [2, 3, 3]),
        (3, [4, 2, 5]),
        (4, [3, 3, 2]),
        (5, [2, 4, 3])
    ]
    
    # 시뮬레이션 실행 후 통계 데이터 반환
    statistics = run_simulation(sim_time, num_machines, jobs_data, arrival_interval)
    
    # 시뮬레이션 결과 출력
    print("\n=== 시뮬레이션 결과 요약 ===")
    for job in statistics['jobs']:
        cycle_time = job.end_time - job.start_time
        print(f"Job {job.id}: 시작 시각 = {job.start_time}, 종료 시각 = {job.end_time}, " 
              f"총 사이클 타임 = {cycle_time}, 각 기계 대기 시간 = {job.waiting_times}")

# 5:00 추가
# 5:36 추가