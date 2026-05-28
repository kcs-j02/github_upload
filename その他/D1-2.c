#include<stdio.h>
#include <string.h>
char search(int n, char s[], char t[]){
  for(int i = 0; i < n; i++){
    if(s[i] != t[i]){
      return s[i];
    }
  }
}

int number(char u, char s[], int n){
  int count = 0;
  for(int i = 0; i < n; i++){
    if(s[i] == u){
      count ++;
    }
  }
  return count;
}

int main(){
  char S[1001], T[1000] , U;

  scanf("%s", S);
  scanf("%s", T);

  int length = strlen(S), count;

  U = search(length, S, T);
  // printf("%c\n", U);
  count = number(U, S, length);

  printf("%d", count);

  return 0;
}