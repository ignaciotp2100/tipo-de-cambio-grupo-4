install.packages("FinCal")
install.packages("FinancialMath")

#title: "Pauta parcial 1 FI sección 1"
#author: "Guillermo Yañez"
#date: "2023-10-11"
#output: word_document

1- Las empresas A y B tienen razones de deuda a activos totales de 40% y 30% y 
rendimientos sobre los activos totales de 12 y 15%, respectivamente.
¿Qué firma tiene un rendimiento más grande sobre el capital? Intérprete. [Hint: Utilizar identidad Dupont]

```{r setup, include=FALSE}
knitr::opts_chunk$set(echo = TRUE)
library(FinCal)
options(scipen=999)
```
deudaAct <- 0.4
deudaBactv <- 0.3
roA <- 0.12
roB <- 0.15

#ROE = roa*multiplicador del capital
# mult= activos/patrimonio
#2/5 
roe_a <- roA*1/(1-deudaAct)
roe_a
roe_B<- roB*1/(1-deudaBactv)
roe_B

2- Una empresa tiene utilidad neta de 205 000 dólares, margen de utilidad de 9.3% 
y saldo en cuentas por cobrar de 162 500 dólares. 
Suponiendo que 80% de las ventas son a crédito, 
¿cuál será la razón de los días de ventas en cuentas por cobrar de la compañía? Intérprete

#para sacar T en formula vp
#100= 150/(1+0.03)^t
#100*(1+0.03)^t= 150
#(1+0.03)^t= 150/100
#log(1+0.03)^t= log(150/100)
#t*log(1+0.03)= log(150/100)
#t= log(150/100)/log(1+0.03)
t= log(150/100)/log(1+0.03)
t

#anualidad
#pago 100 por 3 anos y se dscta 0.05
-pv.annuity(0.05, 3, 100)
#pv= tasa de dscto.   fv= tasa de interes


#SACAR PAGO
#valor presente de anualidad 120, valor futuro 200, tasa 5%, 30 periodos

pmt para el futuro