# Discord Thread Unarchive Applications

Discordのスレッドを自動的にアーカイブ解除をするアプリケーションです。

AWS RDS / Lambda / EC2を使うことが想定されています。

## database

AWS RDSのMySQLにデータベースを構築しています。  
後述のAWS EC2で動かすDiscord Botと、AWS SAMで動かすDiscord Application Commandsがどちらもアクセスできるように同じVPC上に存在する必要があります。

本Appでは他のAppとの兼ね合いで、threadテーブルも使っていますが、unarchiveテーブルだけでも構いません。

## Discord Bot 

AWS EC2上で動作をさせるDiscord Botです。  
スレッドのアップデートを検知すれば良いので、Message Intentsは必要ありません。Guild Intentsがあれば動作します。

databaseへのアクセスは、unarchiveテーブルへのselect権限のみ必要です。

## Discord Application Commands (AWS SAM : lambda)

Discord Application Commands (いわゆるスラッシュコマンド) を処理するアプリケーションです。  
AWS SAM (Serverless Application Model)により実現をしています。

