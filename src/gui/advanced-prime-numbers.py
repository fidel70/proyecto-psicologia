class AdvancedPrimeNumbers:
    def __init__(self):
        self.first_ten_primes = []
        self.primes_from_hundred = []
        self.primes_from_thousend = []
    
    def is_prime(self, number):
        """
        Verifica si un número es primo
        """
        if number < 2:
            return False
        for i in range(2, int(number ** 0.5) + 1):
            if number % i == 0:
                return False
        return True
    
    def get_first_n_primes(self, n):
        """
        Obtiene los primeros n números primos
        """
        self.first_ten_primes = []
        number = 2
        while len(self.first_ten_primes) < n:
            if self.is_prime(number):
                self.first_ten_primes.append(number)
            number += 1
        return self.first_ten_primes
    
    def get_primes_from_number(self, start_number, count):
        """
        Obtiene una cantidad específica de números primos comenzando desde un número dado
        """
        self.primes_from_hundred = []
        number = start_number
        while len(self.primes_from_hundred) < count:
            if self.is_prime(number):
                self.primes_from_hundred.append(number)
            number += 1
        return self.primes_from_hundred
    
    def print_all_results(self):
        """
        Imprime todos los resultados obtenidos
        """
        print("\nLos primeros 10 números primos son:")
        for i, prime in enumerate(self.first_ten_primes, 1):
            print(f"{i}. {prime}")
            
        print("\nLos primeros 10 números primos desde 100 son:")
        for i, prime in enumerate(self.primes_from_hundred, 1):
            print(f"{i}. {prime}")

# Ejemplo de uso
prime_calculator = AdvancedPrimeNumbers()

# Obtener los primeros 10 primos
prime_calculator.get_first_n_primes(10)

# Obtener 10 primos desde 100
prime_calculator.get_primes_from_number(100, 10)

# Mostrar todos los resultados
prime_calculator.print_all_results()
