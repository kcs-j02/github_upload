#include<stdio.h>

void sort(int n, int g[]) {
    int tmp;

    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - 1 - i; j++) {
            if (g[j] < g[j + 1]) {
                tmp = g[j];
                g[j] = g[j + 1];
                g[j + 1] = tmp;
            }
        }
    }
}
void output(int n, int g[]){
  for(int i = 0; i < n; i++){
    printf("%d, ", g[i]);
  }
  printf("\n");
}

int main(){
  int n;
  scanf("%d", &n);
  int g[n];

  for(int i=0; i < n; i++){
    scanf("%d", &g[i]);
  }

  sort(n, g);

  // output(n, g);

  int sum = 0;
  for(int i=0; i< n/2; i++){
    sum = sum + g[2*i];
  }
  printf("%d", sum);

  return 0;
}