class PrimeNumbers:
    def __init__(self):
        self.primes = []
    
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
        self.primes = []
        number = 2
        while len(self.primes) < n:
            if self.is_prime(number):
                self.primes.append(number)
            number += 1
        return self.primes
    
    def print_primes(self):
        """
        Imprime los números primos encontrados
        """
        print("Los primeros 10 números primos son:")
        for i, prime in enumerate(self.primes, 1):
            print(f"{i}. {prime}")

# Ejemplo de uso
prime_calculator = PrimeNumbers()
prime_calculator.get_first_n_primes(10)
prime_calculator.print_primes()
