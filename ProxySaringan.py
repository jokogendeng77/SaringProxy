import requests
import time
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

proxyListCache = None
cacheTime = 1800  # 30 minutes in seconds

def fetchProxyList():
    response = requests.get('https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/xResults/RAW.txt')
    proxies = response.text.split('\n')
    return [proxy for proxy in proxies if proxy.strip() != '']

def testProxy(proxy, websites=['https://google.com', 'https://shopee.co.id']):
    results = []
    total_time = 0
    with ThreadPoolExecutor(max_workers=10) as executor:  # Increase the number of workers to test websites in parallel
        future_to_website = {executor.submit(requests.get, website, proxies={"http": proxy, "https": proxy}, timeout=5): website for website in websites}
        for future in as_completed(future_to_website):
            website = future_to_website[future]
            try:
                response = future.result()
                speed = response.elapsed.total_seconds()
                total_time += speed
                speed_str = f"{speed}"
                if response.status_code == 200:
                    result = {"website": website, "success": True, "speed": speed_str}
                else:
                    result = {"website": website, "success": False, "speed": speed_str, "error": f"Response code: {response.status_code}"}
            except Exception as e:
                result = {"website": website, "success": False, "speed": "N/A", "error": str(e)}
            results.append(result)
    if all(result['success'] for result in results):
        return {"proxy": proxy, "websites": results, "total_time": total_time}
    else:
        return None

def testProxies(proxies):
    start = time.time()
    all_results = []  
    with ThreadPoolExecutor(max_workers=50) as executor:  # Increase max_workers to test more proxies in parallel
        future_to_proxy = {executor.submit(testProxy, proxy): proxy for proxy in proxies}
        for i, future in enumerate(as_completed(future_to_proxy), 1):
            results = future.result()
            if results:
                all_results.append(results)
            success_count = sum(1 for result in all_results if result is not None)
            error_count = i - success_count
            sys.stdout.write(f"\rProgress: [{i}/{len(proxies)}] Success: [{success_count}] Error: [{error_count}]")
            sys.stdout.flush()
    # Sort by total time elapsed in ascending order
    workingProxies = sorted(all_results, key=lambda x: x['total_time']) if all_results else []
    success_rate = len(workingProxies) / len(proxies) if proxies else 0
    print(f"\nTested {len(proxies)} proxies. Success rate: {success_rate:.2%}. Total time: {time.time() - start} seconds")
    return workingProxies

def getWorkingProxies():
    global proxyListCache
    if proxyListCache and time.time() - proxyListCache['time'] < cacheTime:
        print('Using cached proxy list')
        return proxyListCache['data']

    print('Fetching and testing new proxy list')
    proxies = fetchProxyList()
    workingProxies = testProxies(proxies)
    proxyListCache = {'time': time.time(), 'data': workingProxies}

    with open('workingProxies.json', 'w') as f:
        json.dump(workingProxies, f, indent=4)
    print('Saved working proxies to workingProxies.json')

    return workingProxies

getWorkingProxies()

