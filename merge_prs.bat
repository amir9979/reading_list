gh pr list -L 500 | python -c "import os; [os.system('gh pr merge -d -m {0}'.format(input().split()[0][0:])) for i in range(500)]
