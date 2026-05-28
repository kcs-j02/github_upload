#include <stdio.h>

long long count(int N) {
    long long sum = 0;

    for (long long j = 1; j <= N; j++) {
        sum = sum +  j * (N / j);
    }

    return sum;
}

int main() {
    int N;
    scanf("%d", &N);

    printf("%lld\n", count(N));

    return 0;
}