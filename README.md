# ArgDR Index para monitorear el interés internacional en la economía argentina

*Por Andrés Fernández Apenburg*

*Licenciado en Economía, Universidad de Buenos Aires*
## Introducción
Existe una clase de activos financieros llamados ADR (del inglés American Drawing Right). Un ADR es un certificado de titularidad, por parte de un residente estadounidense, de una acción de una empresa cuyas acciones cotizan en un mercado fuera de EEUU. En el caso argentino, se trata de certificados de titularidad de acciones que cotizan en la Bolsa de Comercio de Buenos Aires (BCBA). La compraventa de los ADR argentinos tiene lugar en la Bolsa de Comercio de Nueva York (NYSE) y los valores se expresan en dólares estadounidenses. Existen ADR para múltiples empresas importantes de Argentina, como YPF, Grupo Galicia, e IRSA. 

La cotización de los ADR argentinos es seguida atentamente por los medios de comunicación financieros del país y el exterior, ya que provee una valiosa señal de las expectativas futuras de generación de dólares por parte del sector privado argentino. Sin embargo, no se cuenta con un índice que permita sintetizar el conjunto de los precios, es decir, una única variable numérica, cuya variación día a día refleje la tendencia general de los precios de los múltiples ADR argentinos. 

## La solución propuesta

### Qué buscamos en un índice
Las propiedades deseables de un índice incluyen:
1. Que varíe su valor si varía el estado del fenómeno subyacente a medir (en este caso, las tendencias *generales* del valor de los ADR en su conjunto)
2. Que no se vea afectado por *outliers* (en este caso, firmas pequeñas que aumenten su valor accionario en proporciones mucho mayores que la tendencia general en el resto de las firmas)


### Definición del índice
El Índice ArgDR está definido como un promedio ponderado de todos los precios de ADR argentinos, donde los ponderadores sugeridos son la capitalización de mercado de cada firma como porcentaje de la capitalización bursátil colectiva del total de las firmas incluidas. 
Formalmente, dada una cantidad $N$ de empresas argentinas con ADRs cotizando en el instante o periodo $t$ (por ejemplo, el inicio o cierre de la jornada, o las 12 del mediodía, o un cierto período sobre el cual se toman valores promedio para todos los activos), el índice queda definido como: 

$$ 
ArgDR_{t} = \sum_{i=1}^{N} A_{i, t} \cdot P_{i, t}
$$

Donde $A_{i,t}$ es la cotización en dólares del ADR $i$ en $t$, y $P_{i,t}$ es el ponderador del ADR $i$ en la jornada $t$, definido como:

$$
P_{i, t}=\frac{C_{i, t}}{\sum_{i}^{N}C_{i, t}}
$$

Donde ${C_{i, t}}$ es la capitalización bursátil de la empresa $i$, es decir, su número total de acciones multiplicado por $A_{i, t}$.

Bajo esta definición se cumple que $\sum_{i}^{N}P_{i,t} = 1$, para todo $t$, por lo que se trata de un conjunto válido de ponderadores.

En la práctica, el ponderador se puede tomar como fijo a lo largo de múltiples $t$ (índice tipo Laspeyres), utilizando, por ejemplo, las capitalizaciones bursátiles al cierre del trimestre anterior para calcular los ponderadores, de forma tal que resulta opcional su actualización diaria. 

### Por qué nuestro índice satisface las propiedades deseadas
1. Al tratarse de un promedio ponderado de precios de acciones individuales, si suben todas las acciones, necesariamente debe subir el valor del índice
2. Si una firma es más relevante en el mercado (medido en términos de la capitalización bursátil, esto es, del valor implícito de la compañía en función de la cantidad de acciones y su precio), el índice responderá con un mayor cambio porcentual ante la misma variación porcentual en el valor de dicho activo en comparación con una firma menos relevante, porque el valor de su ponderador será mayor.
