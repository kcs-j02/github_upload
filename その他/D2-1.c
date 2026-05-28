#include <stdio.h>

int main() {
    int N;
    scanf("%d", &N);

    char c[101];

    for (int i = 0; i < N; i++) {
        scanf(" %c", &c[i]);
    }

    for (int i = 0; i < N; i++) {
        printf("%c", c[i]);
    }

    printf("\n");

    return 0;
}