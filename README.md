
# BookAPi

Prosta aplikacja sprawdzająca cene w dniu premiery oraz przeliczająca ją na PLN po koszcie waluty z konktenego dnia.




## Technologie

- Django
- Postgres
- Redis
- Docker
## Uruchomienie
### Pierwszy raz

Należy użyć komendy
```bash
docker compose run django python manage.py migrate
```
Abu zainicjować bazę danych

### Każde kolejne
Należy zmienić zmienną środowiskową `FIRST_USE` na ` False, aby skrócić czas uruchamiania aplikacji (nie ma potrzeby dluższego uruchamiania ze względu na zainicjonowaną bazę danych)
