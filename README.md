# school_meal
感謝群友Meow的協助提供json的規則
讓我可以把校園食材登錄查詢系統接入到HA中
安裝步驟如下:
1. 請先到教育部校園食材登錄網站
   https://fatraceschool.k12ea.gov.tw/frontend/index.html
   進階查詢=>選擇縣市=>選擇區域=>選擇學校院所=>選擇學校名稱=>選擇日期，選好之後按下查詢，會出現下方的網頁,將下圖網址學校號碼的部分複製。
   
   <img src="https://github.com/shihkefa/school_meal/blob/main/schoolNO.png?raw=true" width="800">

2.Homeassistant透過HACS安裝school_meal,安裝完成後重新啟動HA

3.HA的設定=>裝置與服務=>右下方的新增整合=>選擇school_meal=>輸入剛剛步驟1的School號碼
  餐別可以自行依照需求輸入，幼兒園是有早點以及午點的，如果用不到，可以不輸入早點以及午點只輸入午餐的。

實體狀態只有兩種: 分別是有供餐以及無供餐
如果是有供餐，屬性會有菜單、以及照片連結，這樣就可以透過HA去發布通知了

也可以編輯HA面板顯示在HA控制面板中

   <img src="https://github.com/shihkefa/school_meal/blob/main/HAUI-ezgif.com-video-to-gif-converter.gif?raw=true" width="400">





   
