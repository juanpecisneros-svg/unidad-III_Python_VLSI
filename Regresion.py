"""Regression Framework
------------------------------------------------------------------------
Contexto: Crear framework para ejecutar múltiples tests

Framework básico de regresión de tests
"""

import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

class Test:
    """Representa un test individual"""
    
    def __init__(self, name, command, timeout=3600):# timeout por defecto 1 hora y sirve para evitar que un test se quede colgado indefinidamente
        self.name = name
        self.command = command
        self.timeout = timeout
        self.result = None
    
    def run(self, work_dir='.'):
        """Ejecuta el test"""
        print(f"  Running: {self.name}")
        start_time = time.time()
        
        try:
            result = subprocess.run(
                self.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=work_dir
            )
            
            elapsed = time.time() - start_time
            
            self.result = {
                'name': self.name,
                'status': 'PASS' if result.returncode == 0 else 'FAIL',
                'returncode': result.returncode,
                'elapsed': elapsed,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            self.result = {
                'name': self.name,
                'status': 'TIMEOUT',
                'elapsed': elapsed,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Test exceeded timeout of {self.timeout}s'
            }
        
        except Exception as e:
            elapsed = time.time() - start_time
            self.result = {
                'name': self.name,
                'status': 'ERROR',
                'elapsed': elapsed,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
        
        return self.result


class RegressionRunner:
    """Framework para ejecutar regresión de tests"""
    
    def __init__(self, work_dir='regression'):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        self.tests = []
        self.results = []
    
    def add_test(self, name, command, timeout=3600): 
        """Agrega un test a la regresión"""
        test = Test(name, command, timeout)
        self.tests.append(test)
    
    def run_sequential(self):
        """Ejecuta tests secuencialmente"""
        print(f"\n{'='*60}")
        print(f"RUNNING REGRESSION (Sequential)")
        print(f"{'='*60}")
        print(f"Total tests: {len(self.tests)}")
        print(f"Work directory: {self.work_dir}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        for i, test in enumerate(self.tests, 1):
            print(f"[{i}/{len(self.tests)}] {test.name}")
            result = test.run(self.work_dir)
            self.results.append(result)
            
            status_symbol = "PASS" if result['status'] == 'PASS' else "FAIL"
            print(f"    {status_symbol} {result['status']} ({result['elapsed']:.1f}s)\n")
        
        total_time = time.time() - start_time
        self._print_summary(total_time)
    
    def run_parallel(self, max_workers=4):
        """Ejecuta tests en paralelo"""
        print(f"\n{'='*60}")
        print(f"RUNNING REGRESSION (Parallel - {max_workers} workers)")
        print(f"{'='*60}")
        print(f"Total tests: {len(self.tests)}")
        print(f"Work directory: {self.work_dir}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todos los tests al executor para que los ejecute en paralelo
            future_to_test = {
                executor.submit(test.run, self.work_dir): test 
                for test in self.tests
            }
            
            # Recopilar resultados a medida que se
            completed = 0
            for future in as_completed(future_to_test):
                test = future_to_test[future]
                result = future.result()
                self.results.append(result)
                completed += 1
                
                status_symbol = "PASS" if result['status'] == 'PASS' else "FAIL"
                print(f"[{completed}/{len(self.tests)}] {result['name']} "
                      f"{status_symbol} {result['status']} ({result['elapsed']:.1f}s)")
        
        total_time = time.time() - start_time
        print()  # Nueva línea
        self._print_summary(total_time)
    
    def _print_summary(self, total_time):
        """Imprime resumen de regresión"""
        print(f"{'='*60}")
        print("REGRESSION SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        timeout = sum(1 for r in self.results if r['status'] == 'TIMEOUT')
        error = sum(1 for r in self.results if r['status'] == 'ERROR')
        
        print(f"Total:    {len(self.results)}")
        print(f"Passed:   {passed}")
        print(f"Failed:   {failed}")
        print(f"Timeout:  {timeout}")
        print(f"Error:    {error}")
        print(f"\nTotal time: {total_time:.1f}s")
        
        if failed > 0 or timeout > 0 or error > 0:
            print("\nFailed/Timeout/Error tests:")
            for r in self.results:
                if r['status'] != 'PASS':
                    print(f"  - {r['name']}: {r['status']}")
        
        print(f"{'='*60}")
        
        # Estado general
        if passed == len(self.results):
            print(" ALL TESTS PASSED")
        else:
            print(" REGRESSION FAILED")
        print(f"{'='*60}\n")
    
    def save_results(self, filename='regression_results.json'):
        """Guarda resultados en JSON"""
        output_file = self.work_dir / filename
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'passed': sum(1 for r in self.results if r['status'] == 'PASS'),
            'failed': sum(1 for r in self.results if r['status'] == 'FAIL'),
            'timeout': sum(1 for r in self.results if r['status'] == 'TIMEOUT'),
            'error': sum(1 for r in self.results if r['status'] == 'ERROR'),
            'tests': self.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f" Results saved to: {output_file}")

# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == '__main__':
    # Crear runner
    runner = RegressionRunner(work_dir='regression')
    
    # Agregar tests (simulamos con comandos simples para demo)
    runner.add_test('alu_basic', 'echo "Running ALU basic test..." && sleep 1')
    runner.add_test('alu_random', 'echo "Running ALU random test..." && sleep 2')
    runner.add_test('regfile_test', 'echo "Running RegFile test..." && sleep 1')
    runner.add_test('control_test', 'echo "Running Control test..." && sleep 1')
    runner.add_test('integration_test', 'echo "Running Integration test..." && sleep 3')
    
    # Ejecutar (descomentar el que quieras probar)
    runner.run_sequential()  # Secuencial
    #runner.run_parallel(max_workers=3)  # Paralelo
    
    # Guardar resultados
    runner.save_results()